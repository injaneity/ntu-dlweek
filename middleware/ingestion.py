# ingestion.py
import json
import sys
import socket
import threading
from collections import defaultdict

from atproto import AtUri, CAR, firehose_models, FirehoseSubscribeReposClient, models, parse_subscribe_repos_message
from atproto.exceptions import FirehoseError

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
        print(f"Firehose error: {e}")
    finally:
        print("Firehose client stopping.")

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
    print(f"Socket server listening on {host}:{port}")

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
            break

    with clients_lock:
        for client in clients:
            client.close()
        clients.clear()
    server.close()
    print("Socket server closed.")

def main():
    stop_event = threading.Event()
    SOCKET_HOST = 'localhost'
    SOCKET_PORT = 9999

    # Start the socket server in a separate thread.
    server_thread = threading.Thread(target=socket_server, args=(stop_event, SOCKET_HOST, SOCKET_PORT))
    server_thread.daemon = True
    server_thread.start()

    # Start the firehose ingestion process.
    start_firehose_ingestion(stop_event)

    # Keep the main thread alive.
    try:
        while True:
            pass
    except KeyboardInterrupt:
        stop_event.set()
        sys.exit(0)

if __name__ == "__main__":
    main()
