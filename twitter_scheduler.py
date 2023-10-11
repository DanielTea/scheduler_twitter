import streamlit as st
import tweepy
from io import BytesIO
import requests
import time

def get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret) -> tweepy.API:
    """Get twitter conn 1.1"""
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)

def get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret) -> tweepy.Client:
    """Get twitter conn 2.0"""
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    return client

st.title("Post a Tweet")

# Input fields for Twitter API credentials
api_key = st.text_input("API Key")
api_secret = st.text_input("API Secret")
access_token = st.text_input("Access Token")
access_token_secret = st.text_input("Access Token Secret")

# Dynamic input fields for chunks
num_of_chunks = st.number_input("Number of Tweet Chunks", min_value=1, max_value=25, step=1)
chunks = []
for i in range(num_of_chunks):
    chunk = st.text_area(f"Tweet Chunk {i+1}", key=f"chunk_{i}")
    st.write(f"Character count: {len(chunk)}")
    chunks.append(chunk)

# Image upload
image = st.file_uploader("Upload an image", type=['png', 'jpg', 'jpeg'])

if st.button("Send"):
    if api_key and api_secret and access_token and access_token_secret and chunks:
        def post_tweet_logic():
            client_v1 = get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret)
            client_v2 = get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret)

            # If there's an image, upload it
            media_id = None
            if image:
                image_bytes = image.getvalue()
                media = client_v1.media_upload(filename="image.png", file=BytesIO(image_bytes))
                media_id = media.media_id

            # Post the first chunk (with or without image)
            tweet = client_v2.create_tweet(text=chunks[0], media_ids=[media_id] if media_id else None)

            # Post the subsequent chunks as replies
            for reply_content in chunks[1:]:
                if reply_content:  # Ensure the reply_content is not an empty string
                    time.sleep(1.0)  # Pause for a second between tweets to avoid hitting rate limits
                    tweet = client_v2.create_tweet(text=reply_content, in_reply_to_tweet_id=tweet.data["id"])

            st.write("Tweets posted successfully!")

        post_tweet_logic()
    else:
        st.write("Please fill all the necessary fields.")
