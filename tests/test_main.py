#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import GetOldTweets3 as Got3

if sys.version_info[0] < 3:
    raise Exception("Python 2.x is not supported. Please upgrade to 3.x")

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_username():
    tweet_criteria = Got3.manager.TweetCriteria() \
        .set_username('barackobama') \
        .set_max_tweets(1)
    tweet = Got3.manager.TweetManager.get_tweets(tweet_criteria)[0]
    assert tweet.username == 'BarackObama'


def test_query_search():
    tweet_criteria = Got3.manager.TweetCriteria().set_query_search('#europe #refugees') \
        .set_since("2015-05-01") \
        .set_until("2015-09-30") \
        .set_max_tweets(1)
    tweet = Got3.manager.TweetManager.get_tweets(tweet_criteria)[0]
    assert tweet.hashtags.lower() == '#europe #refugees'


def test_mass_fetch_concurrent():
    time1 = time.time()
    tweet_criteria = Got3.manager.TweetCriteria().set_query_search('#europe #refugees') \
        .set_since("2015-05-01") \
        .set_until("2015-09-30") \
        .set_max_tweets(500)
    tweets = Got3.manager.ConcurrentTweetManager.get_tweets(tweet_criteria, worker_count=25)
    print("Time Needed Concurrent: {} Secs".format((time.time() - time1)))
    assert len(tweets) <= 1000


def test_mass_fetch_non_concurrent():
    time1 = time.time()
    tweet_criteria = Got3.manager.TweetCriteria().set_query_search('#europe #refugees') \
        .set_since("2015-05-01") \
        .set_until("2015-09-30") \
        .set_max_tweets(500)
    tweets = Got3.manager.TweetManager.get_tweets(tweet_criteria)
    print("Time Needed Non Concurrent: {} Secs".format((time.time() - time1)))
    assert len(tweets) <= 1000
