# flink_job.py
import json
from pyflink.datastream import StreamExecutionEnvironment, DataStream
from pyflink.common.typeinfo import Types
from better_profanity import profanity
from langdetect import detect, LangDetectException

profanity.load_censor_words()

# Global counter for accepted posts.
count = 0

def filter_and_count(post):
    """
    Apply filtering criteria and remove unwanted fields.

    Filtering criteria:
      - Drop posts with text length < 50 characters.
      - Drop posts if 'langs' does not include 'en'.
    
    For accepted posts, remove from record:
      embed, entities, facets, reply, tags, py_type.
    """
    record = post.get('record', {})
    text = record.get('text', "")
    langs = record.get('langs')

    # primary check
    if len(text) < 50 or not langs or 'en' not in langs or record.get('reply') is not None:
        return None
    
    # secondary language check
    try:
        detected_lang = detect(text)
    except LangDetectException:
        return None
    
    if detected_lang != "en":
        return None
    
    # profanity filter
    if profanity.contains_profanity(text):
        return None

    # clean the data
    for key in ['embed', 'entities', 'facets', 'reply', 'tags', 'py_type']:
        record.pop(key, None)
    post['record'] = record

    return post

def to_json(post):
    """Convert the post dictionary to a JSON string."""
    return json.dumps(post, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))

def parse_post(line: str):
    try:
        post = json.loads(line)
        return post
    except Exception as e:
        return None

def main():
    # Create the Flink execution environment.
    env = StreamExecutionEnvironment.get_execution_environment()
    j_stream_env = env._j_stream_execution_environment

    # Create a socket text stream. This job connects as a client to the ingestion socket.
    SOCKET_HOST = 'localhost'
    SOCKET_PORT = 9999
    j_socket_source = j_stream_env.socketTextStream(SOCKET_HOST, SOCKET_PORT, "\n", 0)
    ds = DataStream(j_socket_source)

    parsed_posts = ds.map(parse_post, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    valid_posts = parsed_posts.filter(lambda post: post is not None)
    processed_posts = valid_posts.map(filter_and_count, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    final_posts = processed_posts.filter(lambda post: post is not None)

    # Convert accepted posts to JSON string.
    json_posts = final_posts.map(lambda post: to_json(post), output_type=Types.STRING())
    json_posts.print()

    env.execute("Bluesky Firehose English Posts Flink Job")

if __name__ == "__main__":
    main()
