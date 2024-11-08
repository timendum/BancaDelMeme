"""
time allows us to record time
logging is the general way we stdout

sqlalchemy is the connection to our MySQL database

praw allows us to connect to reddit

config has all the environmental variables form .env
message has all message constants
utils has some useful functions to make code smaller
kill_handler gracefully handles sigterms
models has database models
main has the reply method
stopwatch is the way we record the time spent on an operation
"""

import asyncio
import html
import logging
import sqlite3
import time
import urllib.parse

import praw
import telegram
from sqlalchemy.orm import scoped_session, sessionmaker
from telegram.constants import ParseMode

import config
import message
from comment_worker import reply_wrap
from kill_handler import KillHandler
from models import Buyable
from stopwatch import Stopwatch
from utils import create_engine, make_reddit, test_reddit_connection

praw.models.Submission.reply_wrap = reply_wrap
logging.basicConfig(level=logging.INFO)


async def post_telegram(conn: sqlite3.Connection, submission, tbot: telegram.Bot):
    link = f"https://reddit.com{urllib.parse.quote(submission.permalink)}"
    title = html.escape(submission.title or "")
    if len(title) <= 3:
        title = "Titolo: " + title
    text = f"<a href='{link}'>{title}</a>"
    logging.info(" -- Posting %s", link)
    msg = None
    if submission.domain == "i.redd.it" or submission.url.split(".")[-1] in (
        "png",
        "jpg",
        "jpeg",
    ):
        try:
            msg = await tbot.send_photo(
                chat_id=config.TG_CHANNEL,
                parse_mode=ParseMode.HTML,
                caption=text,
                photo=submission.url,
            )
        except telegram.error.BadRequest:
            msg = await tbot.send_message(
                chat_id=config.TG_CHANNEL, parse_mode=ParseMode.HTML, text=text
            )
    else:
        msg = await tbot.send_message(
            chat_id=config.TG_CHANNEL, parse_mode=ParseMode.HTML, text=text
        )

    if msg:
        conn.execute(
            "INSERT OR REPLACE INTO posts (rid, tid) values (?, ?)", (submission.id, msg.message_id)
        )
        conn.commit()


async def clean_removed(conn: sqlite3.Connection, tbot: telegram.Bot, reddit: praw.Reddit):
    c = conn.cursor()
    rows = c.execute(
        """SELECT rid, tid
                        FROM posts
                        WHERE tid IS NOT NULL
                        ORDER BY length(rid) desc, rid desc
                        LIMIT 4"""
    )
    deleted = []
    for row in rows:
        try:
            post = reddit.submission(id=row[0])
            if post.removed_by_category:
                logging.info("Deleting %s", row[0])
                deleted.append(row[0])
                await tbot.delete_message(message_id=row[1], chat_id=config.TG_CHANNEL)
        except telegram.error.TelegramError as e_teleg:
            logging.error(e_teleg)
            logging.critical("Telegram error!")
    for post in deleted:
        conn.execute("DELETE FROM posts WHERE rid = ?", (post,))
        conn.commit()
    c.close()


def post_reply(submission):
    # We don't need to post a sticky on stickied posts
    if submission.stickied:
        logging.info(" -- skipping (stickied)")
        return
    if submission.distinguished:
        logging.info(" -- skipping (distinguished)")
        return

    # Post a comment to let people know where to invest
    if config.CLOSED:
        bot_reply = submission.reply_wrap(message.CLOSED_ORG)
    else:
        bot_reply = submission.reply_wrap(message.invest_no_fee(f"u/{submission.author.name}"))

    # Sticky the comment
    if config.IS_MODERATOR:
        bot_reply.mod.distinguish(how="yes", sticky=True)
        bot_reply.mod.approve()
        if config.CLOSED:
            bot_reply.mod.lock()
            bot_reply = None
    logging.info(" -- Reply %s", bot_reply)
    return bot_reply


async def main() -> None:
    """
    This is the main function that listens to new submissions
    and then posts the ATTENTION sticky comment.
    """
    logging.info("Starting submitter...")

    killhandler = KillHandler()

    engine = create_engine()
    sess_maker = scoped_session(sessionmaker(bind=engine))

    reddit = make_reddit()

    logging.info("Setting up database")
    conn = sqlite3.connect(config.POST_DBFILE)
    conn.execute("CREATE TABLE IF NOT EXISTS posts (rid CHAR(10) PRIMARY KEY, tid CHAR(20))")
    conn.commit()

    logging.info("Setting up Telegram connection")
    tbot = telegram.Bot(token=config.TG_TOKEN)
    try:
        me = await tbot.get_me()
        print(me)
    except telegram.error.TelegramError as e_teleg:
        logging.error(e_teleg)
        logging.critical("Telegram error!")
        return

    # We will test our reddit connection here
    if not test_reddit_connection(reddit):
        return

    logging.info("Starting checking submissions...")

    stopwatch = Stopwatch()

    sess = sess_maker()

    subreddits = reddit.subreddit("+".join(config.SUBREDDITS))
    for submission in subreddits.stream.submissions(pause_after=6):
        if killhandler.killed:
            logging.info("Termination signal received - exiting")
            break
        if not submission:
            await clean_removed(conn, tbot, reddit)
            # because of pause_after
            # to handle ctr+c above
            continue
        submission_age = time.time() - int(submission.created_utc)
        max_age = 60 * 60 * 24  # 1 day
        if submission_age > max_age:
            continue

        duration = stopwatch.measure()

        logging.info("New submission: %s", submission)
        logging.info(" -- retrieved in %ss", duration)

        c = conn.cursor()
        c.execute("SELECT tid FROM posts WHERE rid=?", (submission.id,))
        r = c.fetchone()
        if r:
            if not r[0]:
                await post_telegram(conn, submission, tbot)
                continue
            else:
                logging.info("Already processed")
                c.close()
                continue
        c.close()
        try:
            await post_telegram(conn, submission, tbot)
        except Exception:
            logging.exception("Not posted on Telegram: %s", submission.id)
            conn.execute("INSERT INTO posts (rid, tid) values (?, ?)", (submission.id, None))
            conn.commit()

        bot_reply = post_reply(submission)

        # Measure how long processing took
        duration = stopwatch.measure()
        logging.info(" -- processed in %.2fs", duration)

        # Create Buyable
        if bot_reply:
            sess.add(
                Buyable(post=submission.id, name=submission.author.name, response=bot_reply.id)
            )
        sess.commit()


if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception:
            logging.exception("Exception, sleeping and retrying")
            time.sleep(60)
