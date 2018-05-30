import time
import logging
from functools import lru_cache

import MySQLdb
import MySQLdb.cursors
import praw
from bottr.bot import AbstractCommentBot, BotQueueWorker, SubmissionBot
from fastnumbers import fast_float

import config
import message
import models

logging.basicConfig(level=logging.INFO)


class EmptyResponse(object):
    body = ""

    def edit(*args, **kwargs):
        pass


@lru_cache(maxsize=10240)
def calculate(new, old):
    """
    Investment return multiplier is detemined by a power function of the relative change in upvotes since the investment
    was made.
    Functional form: y = x^m ;
        y = multiplier,
        x = relative growth: (change in upvotes) / (upvotes at time of investment),
        m = scale factor: allow curtailing high-growth post returns to make the playing field a bit fairer
    """

    new = fast_float(new)
    old = fast_float(old)

    # Scale factor for multiplier
    scale_factor = 1 / fast_float(3)

    # Calculate relative change
    if old != 0:
        rel_change = (new - old) / abs(old)
    # If starting upvotes was zero, avoid dividing by zero
    else:
        rel_change = new

    mult = pow((rel_change+1), scale_factor)

    return mult


def check_investments(reddit):
    db = MySQLdb.connect(cursorclass=MySQLdb.cursors.DictCursor, **config.dbconfig)

    investments = models.Investments(db)
    investors = models.Investors(db)

    logging.info("Starting checking investments...")
    if config.dry_run:
        praw.models.Comment.edit = logging.info

    while True:
        for row in investments.todo():
            investor = investors[row["name"]]

            print(investor)
            if not investor:
                continue

            if row["response"] != "0":
                response = reddit.comment(id=row["response"])
            else:
                response = EmptyResponse()

            # If comment is deleted, skip it
            try:
                reddit.comment(id=row["comment"])
            except:
                response.edit(message.deleted_comment_org)
                continue

            post = reddit.submission(row["post"])
            upvotes_now = post.ups

            # Updating the investor's balance
            factor = calculate(upvotes_now, row["upvotes"])
            
            # Decide if investment was successful and whether you get anything back at all
            win_threshold = 1.3
            if factor > win_threshold:
                investment_success = True
				return_money = True
            elif factor > 1:
                investment_success = False
                return_money = True
            else:
				investment_success = False
				return_money = False
            
            amount = row["amount"]
            balance = investor["balance"]
            
            # Investor gains money only if investment was successful. If multiplier
			# was below win_threshold but above 1 get back invested mount multiplied by
			# ratio of difference between factor and 1 and difference between win_threshold and 1.
            # Otherwise, if factor was 1 or lower, get back nothing.
            if investment_success:
                new_balance = int( balance + (amount * factor) )
            elif return_money:
                new_balance = int( balance + (amount * ( (factor - 1)/(win_threshold - 1)) )
			else:
			    new_balance = balance
            
            investor["balance"] = new_balance
            change = new_balance - balance

            # Updating the investor's variables
            active = investor["active"]
            if active <= 0:
                investor["active"] = 0
            else:
                investor["active"] = active - 1

            investor["completed"] += 1

            # Marking the investment as done
            investment = investments[row["id"]]
            investment["done"] = 1

            # Editing the comment as a confirmation
            text = response.body
            if investment_success:
                investment["success"] = 1
                logging.info("%s won %d memecoins!" % (investor, change))
                response.edit(message.modify_invest_return(text, change))
            elif return_money:
                lost_memes = int( amount - (amount * (amount * ( (factor - 1)/(win_threshold - 1)) ) )
                logging.info("%s lost %d memecoins..." % (investor, lost_memes))
                response.edit(message.modify_invest_lose(text, lost_memes))
			else:
                logging.info("%s lost %d memecoins..." % (investor, amount))
                response.edit(message.modify_invest_lose(text, amount))

        time.sleep(60)

def main():
    reddit = praw.Reddit(client_id=config.client_id,
                         client_secret=config.client_secret,
                         username=config.username,
                         password=config.password,
                         user_agent=config.user_agent)

    check_investments(reddit)


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logging.error(e)
            time.sleep(10)
