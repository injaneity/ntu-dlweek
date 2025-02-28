import json
import requests
import sys
from pyflink.datastream import StreamExecutionEnvironment, DataStream
from pyflink.common.typeinfo import Types
from better_profanity import profanity
from langdetect import detect, LangDetectException

profanity.load_censor_words()

def filter_and_clean(post):
    """
    Apply filtering criteria and remove unwanted fields.

    Filtering criteria:
      - Drop posts with text length < 50 characters.
      - Drop posts if 'langs' is not provided or does not include 'en'.
      - Drop posts if record's reply is not None.
      - Drop posts if the detected language is not English.
      - Drop posts if the text contains profanity.
    
    For accepted posts, remove from record:
      embed, entities, facets, reply, tags, py_type.
    """
    record = post.get('record', {})
    text = record.get('text', "")
    langs = record.get('langs')
    
    if not langs or 'en' not in langs or len(text) < 50 or record.get('reply') is not None:
        return None

    try:
        detected_lang = detect(text)
    except LangDetectException:
        return None
    if detected_lang != "en":
        return None

    if profanity.contains_profanity(text):
        return None

    # Remove unwanted fields.
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
    except Exception:
        return None

def push_to_http(value):
    """Side-effect function to push a tweet to a REST endpoint."""
    try:
        # Replace the URL with your actual API endpoint.
        requests.post("http://localhost:3000/api/tweets", json={'tweet': value})
    except Exception as e:
        print("HTTP push error:", e)
    return value

def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    j_stream_env = env._j_stream_execution_environment

    # Create a socket text stream from the local ingestion service.
    SOCKET_HOST = 'localhost'
    SOCKET_PORT = 9999
    j_socket_source = j_stream_env.socketTextStream(SOCKET_HOST, SOCKET_PORT, "\n", 0)
    ds = DataStream(j_socket_source)

    parsed_posts = ds.map(parse_post, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    valid_posts = parsed_posts.filter(lambda post: post is not None)
    processed_posts = valid_posts.map(filter_and_clean, output_type=Types.MAP(Types.STRING(), Types.PICKLED_BYTE_ARRAY()))
    final_posts = processed_posts.filter(lambda post: post is not None)

    # Convert accepted posts to JSON.
    json_posts = final_posts.map(lambda post: to_json(post), output_type=Types.STRING())
    
    # Call the REST API for each tweet (side-effect) and then print.
    pushed_posts = json_posts.map(push_to_http, output_type=Types.STRING())
    pushed_posts.print()

    env.execute("Bluesky Firehose English Posts Flink Job")

if __name__ == "__main__":
    main()
