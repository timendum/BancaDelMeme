import sys
sys.path.append('src')

import unittest
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import config
import submitter
import message
from models import Investor, Investment
import mock_praw
from unittest.mock import Mock, MagicMock

class SubmitterTest(unittest.TestCase):
    def setUp(self):
        # create sqlite db
        engine = create_engine(config.DB)
        self.Session = scoped_session(sessionmaker(bind=engine))
        sess = self.Session()
        sess.query(Investment).delete()
        sess.query(Investor).delete()
        sess.commit()
        self.submitter = submitter
        #self.submitter.time.sleep = sleep_func()
        self.reddit = mock_praw.Reddit()
        self.submitter.praw.Reddit = Mock(return_value=self.reddit)
        self.submitter.create_engine = Mock(return_value=engine)
        subm_conn = sqlite3.connect(config.POST_DBFILE)
        subm_conn.execute("DROP TABLE IF EXISTS posts")
        subm_conn.commit()
        subm_conn.close()

    def tearDown(self):
        # remove db file
        sess = self.Session()
        sess.query(Investment).delete()
        sess.query(Investor).delete()
        sess.commit()

    def test_base(self):
        self.submitter.main()
        submission = self.reddit.subreddit().stream.submissions()[0]
        replies = submission.replies
        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[0].body, message.invest_no_fee('u/' + submission.author.name))

    def test_sticky(self):
        submission = self.reddit.subreddit().stream.submissions()[0]
        submission.stickied = True
        self.submitter.main()
        replies = submission.replies
        self.assertEqual(len(replies), 0)

    def test_double(self):
        submission = self.reddit.subreddit().stream.submissions()[0]
        self.submitter.main()
        self.submitter.main()
        replies = submission.replies
        self.assertEqual(len(replies), 1)
