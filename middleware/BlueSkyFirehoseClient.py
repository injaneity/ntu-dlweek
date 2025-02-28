from collections import defaultdict

from atproto import AtUri, CAR, firehose_models, FirehoseSubscribeReposClient, models, parse_subscribe_repos_message
from atproto.exceptions import FirehoseError

# We now only care about posts
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


def run_until_50_posts():
    """
    Connect to the firehose, process commits until a total of 50 posts have been collected,
    then print the collected posts.
    """
    collected_posts = []  # List to store post data
    total_posts = 0

    client = FirehoseSubscribeReposClient(params=None)

    def on_message_handler(message: firehose_models.MessageFrame) -> None:
        nonlocal total_posts

        commit = parse_subscribe_repos_message(message)
        if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
            return
        if not commit.blocks:
            return

        ops = _get_ops_by_type(commit)
        # Check if there are posts in this commit
        post_ops = ops.get(models.ids.AppBskyFeedPost, {})
        created_posts = post_ops.get('created', [])
        num_posts = len(created_posts)
        if num_posts:
            collected_posts.extend(created_posts)
            total_posts += num_posts

        # Stop once we've collected at least 50 posts
        if total_posts >= 50:
            client.stop()
            print("Collected posts from the firehose (total posts: {})".format(total_posts))
            for idx, post in enumerate(collected_posts[:50], start=1):
                print(f"Post {idx}: {post}")
            return

    try:
        client.start(on_message_handler)
    except FirehoseError as e:
        print(f"Firehose error: {e}")

if __name__ == "__main__":
    run_until_50_posts()
