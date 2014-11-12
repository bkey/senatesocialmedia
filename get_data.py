import facebook
import requests
import pymongo
import pandas as pd

from datetime import datetime
import tweepy
import time

client = pymongo.MongoClient()
db = client.dsbc

g = facebook.GraphAPI("FACEBOOK_ACCESS_TOKEN")

auth = tweepy.OAuthHandler("consumer_key", "consumer_secret_key")
auth.set_access_token("access_token","access_token_secret")
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)



#get tweet history, limited by the API to 3200, limited by me to posts later than 2012
def get_tweet_history(twitter_name):
    
    i = 0
    for page in tweepy.Cursor(api.user_timeline, twitter_name, count=100, include_rts=True).pages(300):
        i += 1
        
        for tweet in page:
            if tweet.created_at.year < 2012:
                return tweets 

            #manual check for duplicates, should be handled by mongo but let's be safe!
            if (db.senate_tweets.find({"id": tweet.id_str}).count()) < 1:
                my_tweet = {}
                my_tweet['id'] = tweet.id_str
            
                my_tweet['user'] = twitter_name
                my_tweet['text'] = tweet.text
                my_tweet['retweeted'] = tweet.retweeted
                my_tweet['in_reply_to_user_id'] = tweet.in_reply_to_user_id
                my_tweet['retweet_count'] = tweet.retweet_count
                my_tweet['favorite_count'] = tweet.favorite_count
                my_tweet['created_at'] = tweet.created_at
                my_tweet['id'] = tweet.id_str
                if 'hashtags' in tweet.entities:
                    my_tweet['hashtags'] = tweet.entities.get('hashtags')
                if 'urls' in tweet.entities:
                    my_tweet['urls'] = tweet.entities.get('urls')
                if 'media' in tweet.entities:
                    my_tweet['media'] = tweet.entities.get('media')
                if 'user_mentions' in tweet.entities:
                    my_tweet['user_mentions'] = tweet.entities.get('user_mentions')
        
                db.senate_tweets.insert(tweet)

            else: #once we find a dupe, stop
               return tweets 
            
            last_id = tweet.id

#get facebook page posts, ignore posts by users who are not the page owner
def get_facebook_posts(user_id,date_to_stop):
    feed = g.get_connections(user_id, 'feed')
    
    page_count = 0

    while 'paging' in feed:
                
        for post in feed['data']:
            
            fb_id = post['id']
            u_id = post['from']['id']
            
            if u_id == user_id:
                
                if (db.senate_fb_posts.find({"id": fb_id}).count()) < 1:
                    status_update = {}
                    status_update['user_id'] = user_id
                    status_update['id'] = fb_id
                
                    try:
                        dt = datetime.strptime(post['updated_time'], "%Y-%m-%dT%H:%M:%S+0000")
                        status_update['update_time'] = dt
                        if dt < date_to_stop: 
                            return
                    except:
                        continue
                
                    if 'status_type' in post:
                        status_update['type'] = post['status_type']
                    elif 'type' in post:
                        status_update['type'] = post['type']
                
                    if 'name' in post:
                        status_update['text'] = post['name']
                    elif 'description' in post:
                        status_update['text'] = post['description']
                    elif 'message' in post:
                        status_update['text'] = post['message']  
                
                    if 'story' in post:
                        status_update['story'] = post['story']
                
                    #print status_update
                    db.senate_fb_posts.insert(status_update)
        
        try:
            next_page = feed['paging']['next'] 
            feed = requests.get(next_page).json()
                
            page_count += 1
        except:
            return

