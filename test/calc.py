import sys

sys.path.append("src")

import unittest
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import calculator
import config
from models import Investor, Investment
from mock_praw import Comment, Submission, Reddit, Redditor
from unittest.mock import Mock

class DoneException(BaseException):
    pass


def sleep_func():
    done = False

    def sleep(_):
        nonlocal done
        if not done:
            done = True
            return
        raise DoneException()

    return sleep


class CalculatorTest(unittest.TestCase):
    def setUp(self):
        # create sqlite db
        engine = create_engine(config.DB)
        self.Session = scoped_session(sessionmaker(bind=engine))
        sess = self.Session()
        sess.query(Investment).delete()
        sess.query(Investor).delete()
        sess.commit()
        self.calculator = calculator
        self.calculator.time.sleep = sleep_func()
        self.reddit = Reddit()
        self.calculator.praw.Reddit = Mock(return_value=self.reddit)
        self.calculator.create_engine = Mock(return_value=engine)

    def tearDown(self):
        # remove db entities
        sess = self.Session()
        sess.query(Investment).delete()
        sess.query(Investor).delete()
        sess.commit()

    def create_investment(self, amount, start_upvotes, end_upvotes, iid="0"):
        investor = Investor(name="investor" + iid)
        investor.balance = 0
        submission = Submission("sid" + iid)
        comment = Comment("cid" + iid, investor.name, "dummy", submission)
        self.reddit.add_submission(submission)
        investment = Investment(
            post=comment.submission.id,
            upvotes=start_upvotes,
            comment=comment.id,
            name=comment.author.name,
            amount=amount,
            response="1",
            done=False,
        )
        investment.time = int(time.time()) - config.INVESTMENT_DURATION - 1
        submission.ups = end_upvotes
        sess = self.Session()
        sess.add(investor)
        sess.add(investment)
        sess.commit()
        return investor, investment, submission

    def check_balance(self, sess, investor, lcheck):
        investor_db = sess.query(Investor).filter(Investor.name == investor.name).one()
        self.assertTrue(lcheck(investor_db.balance))

    def test_base(self):
        try:
            investor0, _, _ = self.create_investment(100, 1, 1000, "0")
            investor1, _, _ = self.create_investment(10000, 50, 100, "1")
            self.create_investment(100, 100, 169, "2")
            self.create_investment(100, -1, 100, "3")
            self.create_investment(100, 100, -1, "4")
            self.create_investment(calculator.BALANCE_CAP, 0, 100, "top")
            self.calculator.main()
        except DoneException:
            pass
        sess = self.Session()
        self.check_balance(sess, investor0, lambda balance: balance > 100)
        self.check_balance(sess, investor1, lambda balance: balance < 10000)

    def test_op(self):
        """Test profit greater for OP, same prameters"""
        try:
            investor0, _, submission0 = self.create_investment(100, 1, 200, "op0")
            investor1, _, submission1 = self.create_investment(100, 1, 200, "op1")
            # set investor = OP
            submission1.author = investor1
            self.calculator.main()
        except DoneException:
            pass
        sess = self.Session()
        sess.expire_all()
        balance0 = sess.query(Investor).filter(Investor.name == investor0.name).one().balance
        balance1 = sess.query(Investor).filter(Investor.name == investor1.name).one().balance
        self.assertTrue(balance0 < balance1)
        sess.close()

    def test_loss(self):
        """Test loss equality even for different networth"""
        try:
            investor0, investment0, _ = self.create_investment(100, 1, 5, "loss0")
            investor1, investment1, _ = self.create_investment(100, 1, 5, "loss1")
            sess = self.Session()
            investor0.balance = 100
            investor1.balance = 100000
            sess.commit()
            self.calculator.main()
        except DoneException:
            pass
        sess = self.Session()
        sess.expire_all()
        profit0 = sess.query(Investment).filter(Investment.id == investment0.id).one().profit
        profit1 = sess.query(Investment).filter(Investment.id == investment1.id).one().profit
        self.assertEqual(profit0, profit1)
        sess.close()

    def test_autobroke(self):
        """Test auto broke after big loss"""
        try:
            investor0, _, _ = self.create_investment(100, 100, 100, "0")
            self.calculator.main()
        except DoneException:
            pass
        sess = self.Session()
        sess.expire_all()
        self.check_balance(sess, investor0, lambda balance: balance == 900)
        sess.close()

