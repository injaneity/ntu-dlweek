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
                print("Error broadcasting to a client:", e)
                clients.remove(client)

def _get_ops_by_type(commit: models.ComAtprotoSyncSubscribeRepos.Commit) -> defaultdict:
    """
    Process a commit and extract operations by record type.
    """
    operation_by_type = defaultdict(lambda: {'created': [], 'deleted': []})
    car = CAR.from_bytes(commit.blocks)
    for op in commit.ops:
        if op.action == 'update':
            continue  # Ignore updates

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
    All posts are sent; filtering is handled by the Flink job.
    """
    print("Starting firehose client...")
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
        print(f"Firehose error: {e}")
    finally:
        print("Firehose client stopping.")

def start_firehose_ingestion(stop_event: threading.Event):
    thread = threading.Thread(target=firehose_to_broadcast, args=(stop_event,))
    thread.daemon = True
    thread.start()
    print("Started firehose ingestion thread.")

def socket_server(stop_event: threading.Event, host: str, port: int):
    """
    A socket server that accepts multiple client connections and stores them
    in a global list. It runs until the stop_event is set.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)  # Allow up to 5 queued connections.
    print(f"Socket server listening on {host}:{port}")

    # Accept connections until stop_event is set.
    while not stop_event.is_set():
        try:
            server.settimeout(1.0)
            client, addr = server.accept()
            print(f"Socket server: Client connected from {addr}")
            with clients_lock:
                clients.append(client)
        except socket.timeout:
            continue
        except Exception as e:
            print("Socket server error:", e)
            break

    # Clean up: close all client connections.
    with clients_lock:
        for client in clients:
            client.close()
        clients.clear()
    server.close()
    print("Socket server closed.")

def filter_and_count(post):
    """
    For each post received by the Flink job, print:
      1. The message as received.
      2. The filtering status:
         - "Filtered out: [reason]" if the post is dropped.
         - "Accepted" if it passes the filters.
    Filtering criteria:
      - Drop posts with text length < 50 characters.
      - Drop posts if 'langs' does not include 'en'.
    """
    print("Flink received:", post)

    record = post.get('record', {})
    text = record.get('text', "")
    langs = record.get('langs', ['en'])  # Default to ['en'] if not present.

    if len(text) < 50:
        print("Filtering status: Filtered out due to text length (<50 characters)")
        return None

    if 'en' not in langs:
        print("Filtering status: Filtered out due to missing 'en' in langs")
        return None

    print("Filtering status: Accepted")
    return post

def main():
    stop_event = threading.Event()
    
    SOCKET_HOST = 'localhost'
    SOCKET_PORT = 9999

    # Start the multi-client socket server in a separate thread.
    server_thread = threading.Thread(target=socket_server, args=(stop_event, SOCKET_HOST, SOCKET_PORT))
    server_thread.daemon = True
    server_thread.start()

    # Start the firehose ingestion process.
    start_firehose_ingestion(stop_event)

    # Create the Flink execution environment.
    env = StreamExecutionEnvironment.get_execution_environment()

    # Create a socket text stream (Flink acts as a client here).
    j_stream_env = env._j_stream_execution_environment
    j_socket_source = j_stream_env.socketTextStream(SOCKET_HOST, SOCKET_PORT, "\n", 0)
    ds = DataStream(j_socket_source)

    # Parse JSON messages from the socket.
    def parse_post(line: str):
        print("Flink debug: Raw line from socket:", line)
        try:
            post = json.loads(line)
            print("Flink debug: Successfully parsed post")
            return post
        except Exception as e:
            print(f"Flink error: Failed to parse line: {line}. Error: {e}")
            return None

    parsed_posts = ds.map(parse_post, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    valid_posts = parsed_posts.filter(lambda post: post is not None)

    # Apply filtering and count only the accepted posts.
    processed_posts = valid_posts.map(filter_and_count, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    final_posts = processed_posts.filter(lambda post: post is not None)

    # Print only the accepted posts.
    final_posts.print()

    env.execute("Bluesky Firehose English Posts Job")

if __name__ == "__main__":
    main()
