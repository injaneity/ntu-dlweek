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

def firehose_to_socket(host: str, port: int, stop_event: threading.Event):
    """
    Connect to the Bluesky firehose and write JSON posts to the given TCP socket.
    (This function prints minimal logging; only the Flink pipeline outputs messages.)
    """
    client = FirehoseSubscribeReposClient(params=None)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = False
    while not connected and not stop_event.is_set():
        try:
            sock.connect((host, port))
            connected = True
        except ConnectionRefusedError:
            stop_event.wait(1)

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
        for post in created_posts:
            # Safely extract the record and langs.
            rec = post.get("record") if isinstance(post, dict) else post.record
            # Try to get langs using attribute access if not a dict.
            if isinstance(rec, dict):
                langs = rec.get("langs", ['en'])
            else:
                langs = getattr(rec, "langs", ['en'])
            if not langs or 'en' not in langs:
                continue

            try:
                post_json = json.dumps(post, default=lambda o: o.__dict__)
            except Exception:
                continue
            try:
                sock.sendall((post_json + "\n").encode("utf-8"))
            except Exception:
                continue

            if stop_event.is_set():
                client.stop()
                return

    try:
        client.start(on_message_handler)
    except FirehoseError as e:
        print(f"Firehose error: {e}")
    finally:
        sock.close()

def start_firehose_ingestion(host: str, port: int, stop_event: threading.Event):
    thread = threading.Thread(target=firehose_to_socket, args=(host, port, stop_event))
    thread.daemon = True
    thread.start()

# Global counter for accepted posts.
accepted_count = 0

def process_post(post):
    """
    Process each post received by Flink:
      - Drop posts with text shorter than 50 characters.
      - Drop non-English posts.
      - Remove the "entities" and "facets" fields.
    Print a message indicating whether the post was accepted or filtered out.
    """
    global accepted_count

    # Retrieve the record from the post.
    # It may be a dict or a Pydantic model.
    if isinstance(post, dict) and "record" in post:
        record = post["record"]
    else:
        # Try attribute access.
        record = getattr(post, "record", None)

    if record is None:
        print("Flink: Post filtered out - no record found")
        return None

    # Get text and langs safely.
    if isinstance(record, dict):
        text = record.get("text", "")
        langs = record.get("langs", ["en"])
    else:
        text = getattr(record, "text", "")
        langs = getattr(record, "langs", ["en"])

    if len(text) < 50:
        print("Flink: Post filtered out - text length < 50")
        return None

    if not langs or "en" not in langs:
        print("Flink: Post filtered out - non-English content")
        return None

    # Remove "entities" and "facets" from record.
    # If record is not a dict, convert to dict first.
    if isinstance(record, dict):
        record.pop("entities", None)
        record.pop("facets", None)
    else:
        # Convert to dict; this may vary based on your model.
        record_dict = record.__dict__.copy()
        record_dict.pop("entities", None)
        record_dict.pop("facets", None)
        # Optionally, update the post's record if needed.
        if isinstance(post, dict):
            post["record"] = record_dict
        else:
            # If post is a model, you might not be able to update it in place.
            pass

    accepted_count += 1
    print(f"Flink: Accepted post #{accepted_count}")
    if accepted_count >= 50:
        print("Flink: Reached 50 accepted posts. Stopping job.")
        sys.exit(0)
    return post

def main():
    stop_event = threading.Event()
    
    SOCKET_HOST = 'localhost'
    SOCKET_PORT = 9999

    # Minimal socket server.
    def socket_server(stop_event):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((SOCKET_HOST, SOCKET_PORT))
        server.listen(1)
        conn, _ = server.accept()
        while not stop_event.is_set():
            stop_event.wait(5)
        conn.close()
        server.close()

    server_thread = threading.Thread(target=socket_server, args=(stop_event,))
    server_thread.daemon = True
    server_thread.start()

    start_firehose_ingestion(SOCKET_HOST, SOCKET_PORT, stop_event)

    env = StreamExecutionEnvironment.get_execution_environment()

    # Create a socket text stream using the underlying Java API.
    j_stream_env = env._j_stream_execution_environment
    j_socket_source = j_stream_env.socketTextStream(SOCKET_HOST, SOCKET_PORT, "\n", 0)
    ds = DataStream(j_socket_source)

    def parse_post(line: str):
        try:
            return json.loads(line)
        except Exception:
            return None

    parsed_posts = ds.map(parse_post, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    valid_posts = parsed_posts.filter(lambda post: post is not None)

    # Process posts per requirements.
    processed_posts = valid_posts.map(process_post, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    accepted_posts = processed_posts.filter(lambda post: post is not None)
    accepted_posts.print()

    env.execute("Bluesky Firehose Filtered Posts Job")

if __name__ == "__main__":
    main()
