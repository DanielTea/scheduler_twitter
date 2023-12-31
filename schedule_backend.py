import tweepy
import time
import schedule
from datetime import datetime
from io import BytesIO
import toml

import logging

logging.basicConfig(filename='scheduled_tweets.log', level=logging.ERROR)

from supabase import create_client, Client

import base64

secrets = toml.load("secrets.toml")
# Supabase setup
SUPABASE_URL = secrets["database"]["url"]
SUPABASE_API_KEY = secrets["database"]["api_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

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

def post_scheduled_tweets():
    response = supabase.table('tweets').select("*").lte('scheduled_time', datetime.now().strftime('%Y-%m-%d %H:%M')).execute()
    tweets = response.data

    for tweet in tweets:
        # print(tweet)
        tweet_id, api_key, api_secret, access_token, access_token_secret, scheduled_time, image_data, content, uuid, = tweet.values()

        # print(tweet_id)

        client_v1 = get_twitter_conn_v1(api_key, api_secret, access_token, access_token_secret)
        client_v2 = get_twitter_conn_v2(api_key, api_secret, access_token, access_token_secret)

        media_id = None
        if image_data:
            try:
                image_data = base64.b64decode(image_data)
                media = client_v1.media_upload(filename="image.png", file=BytesIO(image_data))
                media_id = media.media_id
            except Exception as e:
                logging.error(f"Error uploading image for tweet ID {tweet_id}: {e}")


        chunks_response = supabase.table('tweet_chunks').select("*").eq('tweet_id', int(tweet_id)).execute()
        chunks_for_tweet = [chunk['content'] for chunk in chunks_response.data]

        try:
            # Post the first chunk
            tweet_obj = client_v2.create_tweet(text=chunks_for_tweet[0], media_ids=[media_id] if media_id else None)

            # Post the subsequent chunks as replies
            for chunk_content in chunks_for_tweet[1:]:
                time.sleep(1.0)
                tweet_obj = client_v2.create_tweet(text=chunk_content, in_reply_to_tweet_id=tweet_obj.data["id"])
            
            supabase.table('tweets').delete().eq('id', tweet_id).execute()
            supabase.table('tweet_chunks').delete().eq('tweet_id', tweet_id).execute()
        except Exception as e:
            logging.error(f"Error posting tweet ID {tweet_id}: {e}")

# Set the function to run every minute
schedule.every(1).minutes.do(post_scheduled_tweets)

while True:
    schedule.run_pending()
    time.sleep(5)
