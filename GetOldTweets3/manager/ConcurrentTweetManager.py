# Author: Giulio Neusch-Frediani - www.github.com/giulionf
from datetime import datetime
from threading import Thread
from queue import Queue
from queue import Empty
import copy

from GetOldTweets3.manager.TweetManager import TweetManager

DATE_FORMAT = "%Y-%m-%d"
FIRST_TWEET_DATE = datetime.strptime("2006-03-21", DATE_FORMAT)

time_spans = Queue()
tweets = []
workers = []


class ConcurrentTweetManager:

    @staticmethod
    def getTweets(tweetCriteria, receiveBuffer=None, bufferLength=100, proxy=None, debug=False, worker_count=1):
        # Split the date in smaller parts
        since_date = datetime.strptime(tweetCriteria.since, DATE_FORMAT) if tweetCriteria.since else FIRST_TWEET_DATE
        until_date = datetime.strptime(tweetCriteria.until, DATE_FORMAT) if tweetCriteria.until else datetime.now()
        date_diff_per_worker = (until_date - since_date) / worker_count

        # Create a TweetCriteria that can be cloned as Model by the Workers
        criteria = copy.deepcopy(tweetCriteria)
        criteria.setMaxTweets(criteria.maxTweets / worker_count)

        # Create a time span for each of the splitted parts and a corresponding worker
        for i in range(1, worker_count+1):
            global time_spans
            global workers
            from_time = since_date + (i-1) * date_diff_per_worker
            to_time = since_date + i * date_diff_per_worker
            time_spans.put((from_time, to_time))

            w = WorkerThread(copy.deepcopy(criteria), receiveBuffer, bufferLength, proxy, debug)
            w.start()
            workers.append(w)

        # Wait for the workers to finish and then stop them
        time_spans.join()
        for worker in workers:
            worker.stop()

        return tweets


class WorkerThread(Thread):

    def __init__(self, tweetCriteria, receiveBuffer=None, bufferLength=100, proxy=None, debug=False):
        super().__init__()
        self.stopped = False
        self.manager = TweetManager()
        self.tweetCriteria = tweetCriteria
        self.receiveBuffer = receiveBuffer
        self.bufferLength = bufferLength
        self.proxy = proxy
        self.debug = debug

    def stop(self):
        self.stopped = True

    def run(self) -> None:
        global time_spans
        global tweets

        while not self.stopped:
            try:
                time_span = time_spans.get_nowait()
                self.tweetCriteria.setSince(datetime.strftime(time_span[0], "%Y-%m-%d"))
                self.tweetCriteria.setUntil(datetime.strftime(time_span[1], "%Y-%m-%d"))
                search_results = self.manager.getTweets(self.tweetCriteria, self.receiveBuffer, self.bufferLength,
                                                        self.proxy, self.debug)
                tweets.extend(search_results)
                time_spans.task_done()
            except Empty:
                pass
