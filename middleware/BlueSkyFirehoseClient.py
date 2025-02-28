import logging
from collections import defaultdict
from threading import Event

from atproto import AtUri, CAR, firehose_models, FirehoseSubscribeReposClient, models, parse_subscribe_repos_message
from atproto.exceptions import FirehoseError

# Define the record types we're interested in
_INTERESTED_RECORDS = {
    models.AppBskyFeedLike: models.ids.AppBskyFeedLike,
    models.AppBskyFeedPost: models.ids.AppBskyFeedPost,
    models.AppBskyGraphFollow: models.ids.AppBskyGraphFollow,
}


def _get_ops_by_type(commit: models.ComAtprotoSyncSubscribeRepos.Commit) -> defaultdict:
    """
    Process a commit and extract operations by record type.
    """
    operation_by_type = defaultdict(lambda: {'created': [], 'deleted': []})
    car = CAR.from_bytes(commit.blocks)
    for op in commit.ops:
        if op.action == 'update':
            # Ignore updates
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
                    operation_by_type[record_nsid]['created'].append({'record': record, **create_info})
                    break

        elif op.action == 'delete':
            operation_by_type[uri.collection]['deleted'].append({'uri': str(uri)})

    return operation_by_type


def run_first_50():
    """
    Connect to the firehose, process the first 50 messages, and print the operations.
    """
    collected_operations = []
    message_count = 0

    # No stored state is used in this standalone version
    params = None
    client = FirehoseSubscribeReposClient(params)

    def on_message_handler(message: firehose_models.MessageFrame) -> None:
        nonlocal message_count

        if message_count >= 50:
            client.stop()
            return

        commit = parse_subscribe_repos_message(message)
        if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
            return

        if not commit.blocks:
            return

        ops = _get_ops_by_type(commit)
        collected_operations.append(ops)
        message_count += 1

        if message_count >= 50:
            client.stop()
            print("Collected operations from the first 50 messages:")
            for idx, op in enumerate(collected_operations, start=1):
                print(f"Message {idx}: {dict(op)}")

    try:
        client.start(on_message_handler)
    except FirehoseError as e:
        print(f"Firehose error: {e}")

if __name__ == "__main__":
    run_first_50()
