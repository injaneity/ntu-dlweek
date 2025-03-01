# Clearsky
Hate comments are a dime a dozen on sites such as X (formerly Twitter) and Bluesky (Twitter's cooler step-brother), and impressionable youths are susceptible to negative rhetoric, from celebrities to bot comments spreading discord. **Clearsky** filters out hateful comments in real-time, the perfect option to scroll your favourite content, whilst drowning out the noise of vitriol.

### Quick Setup
**Requirements**: 
Python 3.11.X
Node v18 and above

For Mac/Linux:
```
chmod +x run.sh
./run.sh
```

For Windows:
```
./run.bat
```

## Machine Learning


## ATProto
ATProto is an open-source protocol built by the engineers over at Bluesky, which aims to democratise user data and provide access to all. We make use of Bluesky's own relay to quickly pull large volumes of user posts, as a proof of concept for Clearsky's ability to filter in real time. Posts gathered from the Bluesky relay (or Firehose) are not meaningfully sorted or categorised, and appear on the frontend in real time.

## Apache Flink (PyFlink)
To process real time data, a stream processing pipeline is required to quickly pre-process incoming data effectively and feed our ML model clean data for faster inference. Apache Flink was used to filter out "spammy" messages (less than 50 characters), non-English data and perform preliminary checks with a profanity filter. The data obtained from Bluesky's firehose is then cleaned and sent to the ML model to be processed. Uses the PyFlink library to link with Bluesky's Python support.

### Notes
Names, handles and profile photos of posts on Clearsky are kept anonymous to protect the identity of Bluesky users, regardless of the content of their posts. Clearsky is meant to be a tool to showcase the potential of real-time filtering and how social media platforms can work to improve their automated moderation tools.