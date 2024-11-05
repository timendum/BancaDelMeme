"""
datetime gives us access to current month
traceback flushes errors
logging is the general stdout for us

prawcore has the list of praw exceptions
"""
import logging
import time
import traceback

import praw
import prawcore
from sqlalchemy import create_engine as __create_engine

import config

logging.basicConfig(level=logging.INFO)

DEPLOY_DATE = time.strftime("%c")
BALANCE_CAP = 1000 * 1000 * 1000 * 1000 * 1000 * 1000  # One quintillion MemeCoins


def investment_duration_string(duration) -> str:
    """
    We may change the investment duration in the future
    and this function allows us to have agile strings
    depending on the duration from .env
    """
    hours = duration // 3600
    duration %= 3600
    minutes = duration // 60
    duration %= 60

    inv_string = ""
    if hours:
        inv_string += f"{hours} or"
        if hours > 1:
            inv_string += "e"
        else:
            inv_string += "a"
        inv_string += " "
    if minutes:
        inv_string += f"{minutes} minut"
        if minutes > 1:
            inv_string += "i"
        else:
            inv_string += "o"
        inv_string += " "
    if duration:
        inv_string += f"{duration} second"
        if duration > 1:
            inv_string += "i"
        else:
            inv_string += "o"
        inv_string += " "

    return inv_string


def test_reddit_connection(reddit) -> bool:
    """
    This function just tests connection to reddit
    Many things can happen:
     - Wrong credentials
     - Absolutly garbage credentials
     - No internet

    This function helps us to quickly check if we are online
    Return true on success and false on failure
    """
    try:
        reddit.user.me()
    except prawcore.exceptions.OAuthException as e_creds:
        traceback.print_exc()
        logging.error(e_creds)
        logging.critical("Invalid login credentials. Check your .env!")
        logging.critical("Fatal error. Cannot continue or fix the problem. Bailing out...")
        return False
    return True


def keep_up(function) -> None:
    """Log exceptions and execute the function again."""
    while True:
        try:
            return function()
        except Exception:
            logging.exception("Exception, sleeping and retrying")
            time.sleep(60)


def formatNumber(n) -> str:
    """Format Mem€ in a short format"""
    suffixes = {6: "M", 9: "B", 12: "T", 15: "Q", 18: "E"}
    digits = len(str(n))
    if digits <= 6:
        return f"{n:,}"
    exponent = (digits - 1) - ((digits - 1) % 3)
    mantissa = n / (10**exponent)
    suffix = suffixes.get(exponent)
    return f"{mantissa:.2f}{suffix}"


class EmptyResponse:
    """Mock up of reddit message"""

    def __init__(self):
        self.body = "[fake response body]"
        self.parent = self

    def edit_wrap(self, body):
        """Log to console"""
        logging.info(" -- editing fake response")
        logging.info(body)

    def reply_wrap(self, body):
        """Log to console"""
        logging.info(" -- posting fake response")
        logging.info(body)


def edit_wrap(self, body):
    """Utility method to check configuration before posting to Reddit"""
    logging.info(" -- editing response")

    if config.POST_TO_REDDIT:
        try:
            return self.edit(body=body)
        # TODO: get rid of this broad except
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
            logging.info(" -- 2nd try in 30 seconds")
            time.sleep(30)
            try:
                return self.edit(body=body)
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                return False
    else:
        logging.info(body)
        return False


def create_engine():
    return __create_engine(config.DB)


def make_reddit() -> praw.Reddit:
    return praw.Reddit(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        username=config.USERNAME,
        password=config.PASSWORD,
        user_agent=config.USER_AGENT,
        check_for_async=False
    )
