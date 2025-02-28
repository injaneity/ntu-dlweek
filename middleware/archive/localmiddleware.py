import json
import sys
import socket
import threading
from collections import defaultdict

from atproto import AtUri, CAR, firehose_models, FirehoseSubscribeReposClient, models, parse_subscribe_repos_message
from atproto.exceptions import FirehoseError

from pyflink.datastream import StreamExecutionEnvironment, DataStream
from pyflink.common.typeinfo import Types

# Only care about post records
_INTERESTED_RECORDS = {
    models.AppBskyFeedPost: models.ids.AppBskyFeedPost,
}

# Global list of connected clients and a lock for thread-safety.
clients = []
clients_lock = threading.Lock()

# Global counter for accepted posts.
count = 0

def broadcast_message(message: str):
    """
    Broadcast a message to all connected clients.
    If sending to a client fails, remove it from the list.
    """
    with clients_lock:
        for client in list(clients):
            try:
                client.sendall((message + "\n").encode("utf-8"))
            except Exception as e:
                clients.remove(client)

def _get_ops_by_type(commit: models.ComAtprotoSyncSubscribeRepos.Commit) -> defaultdict:
    """
    Process a commit and extract operations by record type.
    """
    operation_by_type = defaultdict(lambda: {'created': [], 'deleted': []})
    car = CAR.from_bytes(commit.blocks)
    for op in commit.ops:
        if op.action == 'update':
            continue

        uri = AtUri.from_str(f'at://{commit.repo}/{op.path}')

        if op.action == 'create':
            if not op.cid:
                continue

            create_info = {'uri': str(uri), 'cid': str(op.cid), 'author': commit.repo}
            record_raw_data = car.blocks.get(op.cid)
            if not record_raw_data:
                continue

            record = models.get_or_create(record_raw_data, strict=False)
            if record is None:
                continue

            for record_type, record_nsid in _INTERESTED_RECORDS.items():
                if uri.collection == record_nsid and models.is_record_type(record, record_type):
                    operation_by_type[record_nsid]['created'].append({
                        'record': record,
                        **create_info
                    })
                    break

        elif op.action == 'delete':
            operation_by_type[uri.collection]['deleted'].append({'uri': str(uri)})

    return operation_by_type

def firehose_to_broadcast(stop_event: threading.Event):
    """
    Connect to the Bluesky firehose and broadcast JSON posts to all connected socket clients.
    """
    client = FirehoseSubscribeReposClient(params=None)

    def on_message_handler(message: firehose_models.MessageFrame) -> None:
        if stop_event.is_set():
            client.stop()
            return

        commit = parse_subscribe_repos_message(message)
        if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
            return
        if not commit.blocks:
            return

        ops = _get_ops_by_type(commit)
        post_ops = ops.get(models.ids.AppBskyFeedPost, {})
        created_posts = post_ops.get('created', [])
        if not created_posts:
            return

        for post in created_posts:
            try:
                post_json = json.dumps(post, default=lambda o: o.__dict__)
            except Exception:
                continue

            broadcast_message(post_json)

            if stop_event.is_set():
                client.stop()
                return

    try:
        client.start(on_message_handler)
    except FirehoseError as e:
        pass
    finally:
        pass

def start_firehose_ingestion(stop_event: threading.Event):
    thread = threading.Thread(target=firehose_to_broadcast, args=(stop_event,))
    thread.daemon = True
    thread.start()

def socket_server(stop_event: threading.Event, host: str, port: int):
    """
    A socket server that accepts multiple client connections and stores them
    in a global list. It runs until the stop_event is set.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    
    while not stop_event.is_set():
        try:
            server.settimeout(1.0)
            client, _ = server.accept()
            with clients_lock:
                clients.append(client)
        except socket.timeout:
            continue
        except Exception as e:
            break

    with clients_lock:
        for client in clients:
            client.close()
        clients.clear()
    server.close()

def filter_and_count(post):
    """
    Apply filtering criteria and remove unwanted fields.
    
    Filtering criteria:
      - Drop posts with text length < 50 characters.
      - Drop posts if 'langs' does not include 'en'.
    
    For accepted posts, remove from record:
      embed, entities, facets, reply, tags, py_type.
    Increment the accepted count, and when 50 accepted posts are reached,
    exit the job.
    """
    global count

    record = post.get('record', {})
    text = record.get('text', "")
    langs = record.get('langs') or ['en']

    if len(text) < 50 or 'en' not in langs:
        return None

    for key in ['embed', 'entities', 'facets', 'reply', 'tags', 'py_type']:
        record.pop(key, None)
    post['record'] = record

    count += 1
    print(count)
    if count >= 50:
        sys.exit(0)
    return post

def main():
    stop_event = threading.Event()
    SOCKET_HOST = 'localhost'
    SOCKET_PORT = 9999

    server_thread = threading.Thread(target=socket_server, args=(stop_event, SOCKET_HOST, SOCKET_PORT))
    server_thread.daemon = True
    server_thread.start()

    start_firehose_ingestion(stop_event)

    env = StreamExecutionEnvironment.get_execution_environment()
    j_stream_env = env._j_stream_execution_environment
    j_socket_source = j_stream_env.socketTextStream(SOCKET_HOST, SOCKET_PORT, "\n", 0)
    ds = DataStream(j_socket_source)

    def parse_post(line: str):
        try:
            post = json.loads(line)
            return post
        except Exception as e:
            return None

    parsed_posts = ds.map(parse_post, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    valid_posts = parsed_posts.filter(lambda post: post is not None)
    processed_posts = valid_posts.map(filter_and_count, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    final_posts = processed_posts.filter(lambda post: post is not None)

    # Convert each accepted post to a JSON string before printing.
    def to_json(post):
        return json.dumps(post, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
    
    json_posts = final_posts.map(lambda post: to_json(post), output_type=Types.STRING())
    json_posts.print()

    env.execute("Bluesky Firehose English Posts Job")

if __name__ == "__main__":
    main()
