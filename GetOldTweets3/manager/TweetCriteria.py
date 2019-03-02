class TweetCriteria:
    """Search parameters class"""

    def __init__(self):
        self.max_tweets = 0
        self.top_tweets = False
        self.within = "15mi"
        self.username = None
        self.since = None
        self.until = None
        self.near = None
        self.query_search = None
        self.lang = None

    def set_username(self, username):
        """Set username(s) of tweets author(s)

        Examples:
            setUsername('barackobama')
            setUsername('barackobama,whitehouse')
            setUsername('barackobama whitehouse')
            setUsername(['barackobama','whitehouse'])

        Parameters
        ----------
        username : str or iterable

        If `username' is specified by str it should be a single username or
        usernames separeated by spaces or commas.
        `username` can contain a leading @

        """
        self.username = username
        return self

    def set_since(self, since):
        """Set a lower bound date in UTC
        Parameters
        ----------
        since : str,
                format: "yyyy-mm-dd"
        """
        self.since = since
        return self

    def set_until(self, until):
        """Set an upper bound date in UTC (not included in results)
        Parameters
        ----------
        until : str,
                format: "yyyy-mm-dd"
        """
        self.until = until
        return self

    def set_near(self, near):
        """Set location to search nearby
        Parameters
        ----------
        near : str,
               for example "Berlin, Germany"
        """
        self.near = near
        return self

    def set_within(self, within):
        """Set the radius for search by location
        Parameters
        ----------
        within : str,
                 for example "15mi"
        """
        self.within = within
        return self

    def set_query_search(self, query_search):
        """Set a text to be searched for
        Parameters
        ----------
        query_search : str
        """
        self.query_search = query_search
        return self

    def set_max_tweets(self, max_tweets):
        """Set the maximum number of tweets to search
        Parameters
        ----------
        max_tweets : int
        """
        self.max_tweets = max_tweets
        return self

    def set_lang(self, lang):
        """Set language
        Parameters
        ----------
        lang : str
        """
        self.lang = lang
        return self

    def set_top_tweets(self, top_tweets):
        """Set the flag to search only for top tweets
        Parameters
        ----------
        top_tweets : bool
        """
        self.top_tweets = top_tweets
        return self
