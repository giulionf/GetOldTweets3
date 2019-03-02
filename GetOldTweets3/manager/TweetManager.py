# -*- coding: utf-8 -*-

import datetime
import http.cookiejar
import json
import random
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from pyquery import PyQuery

from .. import models


class TweetManager:
    """A class for accessing the Twitter's search engine"""

    def __init__(self):
        pass

    user_agents = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:62.0) Gecko/20100101 Firefox/62.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:61.0) Gecko/20100101 Firefox/61.0',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/70.0.3538.77 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/12.0 Safari/605.1.15',
    ]

    @staticmethod
    def get_tweets(tweet_criteria, receive_buffer=None, buffer_length=100, proxy=None, debug=False):
        """Get tweets that match the tweetCriteria parameter
        A static method.

        Parameters
        ----------
        tweet_criteria : tweetCriteria, an object that specifies a match criteria
        receive_buffer : callable, a function that will be called upon a getting next `bufferLength' tweets
        buffer_length: int, the number of tweets to pass to `receiveBuffer' function
        proxy: str, a proxy server to use
        debug: bool, output debug information
        """
        results = []
        results_aux = []
        cookie_jar = http.cookiejar.CookieJar()
        user_agent = random.choice(TweetManager.user_agents)

        all_usernames = []
        usernames_per_batch = 20

        if tweet_criteria.username:
            if type(tweet_criteria.username) == str or not hasattr(tweet_criteria.username, '__iter__'):
                tweet_criteria.username = [tweet_criteria.username]

            usernames_ = [u.lstrip('@') for u in tweet_criteria.username if u]
            all_usernames = sorted({u.lower() for u in usernames_ if u})
            n_usernames = len(all_usernames)
            n_batches = n_usernames // usernames_per_batch + (n_usernames % usernames_per_batch > 0)
        else:
            n_batches = 1

        for batch in range(n_batches):  # process all_usernames by batches
            refresh_cursor = ''
            batch_cnt_results = 0

            if all_usernames:  # a username in the criteria?
                tweet_criteria.username \
                    = all_usernames[batch * usernames_per_batch:batch * usernames_per_batch + usernames_per_batch]

            active = True
            while active:
                json_ = TweetManager.get_json_response(tweet_criteria, refresh_cursor, cookie_jar, proxy, user_agent,
                                                       debug=debug)
                if len(json_['items_html'].strip()) == 0:
                    break

                refresh_cursor = json_['min_position']
                scraped_tweets = PyQuery(json_['items_html'])
                # Remove incomplete tweets withheld by Twitter Guidelines
                scraped_tweets.remove('div.withheld-tweet')
                tweets = scraped_tweets('div.js-stream-tweet')

                if len(tweets) == 0:
                    break

                for tweetHTML in tweets:
                    tweet_pq = PyQuery(tweetHTML)
                    tweet = models.Tweet()

                    usernames = tweet_pq("span.username.u-dir b").text().split()
                    if not len(usernames):  # fix for issue #13
                        continue

                    tweet.username = usernames[0]
                    tweet.to = usernames[1] if len(usernames) >= 2 else None  # take the first recipient if many
                    tweet.text = re.sub(r"\s+", " ", tweet_pq("p.js-tweet-text").text()) \
                        .replace('# ', '#').replace('@ ', '@').replace('$ ', '$')
                    tweet.retweets = int(
                        tweet_pq("span.ProfileTweet-action--retweet span.ProfileTweet-actionCount").attr(
                            "data-tweet-stat-count").replace(",", ""))
                    tweet.favorites = int(
                        tweet_pq("span.ProfileTweet-action--favorite span.ProfileTweet-actionCount").attr(
                            "data-tweet-stat-count").replace(",", ""))
                    tweet.replies = int(tweet_pq("span.ProfileTweet-action--reply span.ProfileTweet-actionCount").attr(
                        "data-tweet-stat-count").replace(",", ""))
                    tweet.id = tweet_pq.attr("data-tweet-id")
                    tweet.permalink = 'https://twitter.com' + tweet_pq.attr("data-permalink-path")
                    tweet.author_id = int(tweet_pq("a.js-user-profile-link").attr("data-user-id"))

                    date_sec = int(tweet_pq("small.time span.js-short-timestamp").attr("data-time"))
                    tweet.date = datetime.datetime.fromtimestamp(date_sec, tz=datetime.timezone.utc)
                    tweet.formatted_date = datetime.datetime.fromtimestamp(date_sec, tz=datetime.timezone.utc) \
                        .strftime("%a %b %d %X +0000 %Y")
                    tweet.mentions = " ".join(re.compile('(@\\w*)').findall(tweet.text))
                    tweet.hashtags = " ".join(re.compile('(#\\w*)').findall(tweet.text))

                    geo_span = tweet_pq('span.Tweet-geo')
                    if len(geo_span) > 0:
                        tweet.geo = geo_span.attr('title')
                    else:
                        tweet.geo = ''

                    urls = []
                    for link in tweet_pq("a"):
                        try:
                            urls.append((link.attrib["data-expanded-url"]))
                        except KeyError:
                            pass

                    tweet.urls = ",".join(urls)

                    results.append(tweet)
                    results_aux.append(tweet)

                    if receive_buffer and len(results_aux) >= buffer_length:
                        receive_buffer(results_aux)
                        results_aux = []

                    batch_cnt_results += 1
                    if 0 < tweet_criteria.max_tweets <= batch_cnt_results:
                        active = False
                        break

            if receive_buffer and len(results_aux) > 0:
                receive_buffer(results_aux)
                results_aux = []

        return results

    @staticmethod
    def get_json_response(tweet_criteria, refresh_cursor, cookie_jar, proxy, useragent=None, debug=False):
        """Invoke an HTTP query to Twitter.
        Should not be used as an API function. A static method.
        """
        url = "https://twitter.com/i/search/timeline?"

        if not tweet_criteria.top_tweets:
            url += "f=tweets&"

        url += ("vertical=news&q=%s&src=typd&%s"
                "&include_available_features=1&include_entities=1&max_position=%s"
                "&reset_error_state=false")

        url_get_data = ''

        if tweet_criteria.query_search:
            url_get_data += tweet_criteria.query_search

        if tweet_criteria.username:
            if not tweet_criteria.username:
                tweet_criteria.username = [tweet_criteria.username]

            usernames_ = [u.lstrip('@') for u in tweet_criteria.username if u]
            tweet_criteria.username = {u.lower() for u in usernames_ if u}

            usernames = [' from:' + u for u in sorted(tweet_criteria.username)]
            if usernames:
                url_get_data += ' OR'.join(usernames)

        if tweet_criteria.near and tweet_criteria.within:
            url_get_data += ' near:%s within:%s' % (tweet_criteria.near, tweet_criteria.within)

        if tweet_criteria.since:
            url_get_data += ' since:' + tweet_criteria.since

        if tweet_criteria.until:
            url_get_data += ' until:' + tweet_criteria.until

        if tweet_criteria.lang:
            url_lang = 'l=' + tweet_criteria.lang + '&'
        else:
            url_lang = ''
        url = url % (urllib.parse.quote(url_get_data.strip()), url_lang, urllib.parse.quote(refresh_cursor))
        useragent = useragent or TweetManager.user_agents[0]

        headers = [
            ('Host', "twitter.com"),
            ('User-Agent', useragent),
            ('Accept', "application/json, text/javascript, */*; q=0.01"),
            ('Accept-Language', "en-US,en;q=0.5"),
            ('X-Requested-With', "XMLHttpRequest"),
            ('Referer', url),
            ('Connection', "keep-alive")
        ]

        if proxy:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}),
                                                 urllib.request.HTTPCookieProcessor(cookie_jar))
        else:
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        opener.addheaders = headers

        if debug:
            print(url)
            print('\n'.join(h[0] + ': ' + h[1] for h in headers))

        try:
            response = opener.open(url)
            json_response_ = response.read()
        except Exception as e:
            print("An error occured during an HTTP request:", str(e))
            print("Try to open in browser: https://twitter.com/search?q=%s&src=typd" % urllib.parse.quote(url_get_data))
            sys.exit()

        try:
            s_json = json_response_.decode()
        except ValueError:
            print("Invalid response from Twitter")
            sys.exit()

        try:
            data_json = json.loads(s_json)
        except ValueError:
            print("Error parsing JSON: %s" % s_json)
            sys.exit()

        if debug:
            print(s_json)
            print("---\n")

        return data_json
