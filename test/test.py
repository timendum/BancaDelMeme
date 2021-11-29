import sys

sys.path.append("src")

import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import config
from comment_worker import CommentWorker
from models import Base, Investor, Investment
from mock_praw import Comment, Submission


class Test(unittest.TestCase):
    def setUp(self):
        # create sqlite db
        engine = create_engine(config.DB)
        self.Session = session_maker = scoped_session(sessionmaker(bind=engine))
        Base.metadata.create_all(engine)
        sess = self.Session()
        sess.query(Investment).delete()
        sess.query(Investor).delete()
        self.comments = []
        self.submissions = []

        self.worker = CommentWorker(session_maker)

    def tearDown(self):
        # remove db file
        sess = self.Session()
        sess.query(Investment).delete()
        sess.query(Investor).delete()
        sess.commit()

    def command(self, command, username="testuser", post="testpost", lcomment=None, lpost=None):
        submission = Submission(post)
        self.submissions.append(submission)
        if lpost:
            lpost(submission)
        comment = Comment(post + "/id", username, command, submission)
        submission.replies.append(comment)
        self.comments.append(comment)
        if lcomment:
            lcomment(comment)
        self.worker(comment)
        return comment.replies

    def set_balance(self, balance, username="testuser"):
        sess = self.Session()
        investor = sess.query(Investor).filter(Investor.name == username).first()
        investor.balance = balance
        sess.commit()
