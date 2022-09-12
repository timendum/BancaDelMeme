import logging
import time

import praw
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import sessionmaker

import config
from models import Investment, Investor
from utils import create_engine, formatNumber, make_reddit, test_reddit_connection

logging.basicConfig(level=logging.INFO)
localtime = time.strftime("{%Y-%m-%d %H:%M:%S}")

wiki_lead_text_org = """
#Migliori utenti:

%TOP_USERS%  

Ultimo aggiornamento: %LOCALTIME%
"""

wiki_oc_text_org = """
#Migliori autori:

%TOP_OC%  

Ultimo aggiornamento: %LOCALTIME%
"""


def format_investor(users, limit=1000) -> str:
    text = ".|Utente|Patrimonio\n"
    text += ":-:|:-:|:-:\n"
    for i, user in enumerate(users):
        text += f"{i + 1}|/u/{user.name}|{formatNumber(user.networth)} M€\n"
        if i + 1 >= limit:
            break
    return text


def format_posters_small(users, limit=500) -> str:
    text = ".|Autore|#OC|Karma|\n"
    text += ":-:|:-:|:-:|:-:\n"
    for i, user in enumerate(users):
        text += f"{i + 1}|/u/{user[0]}|{user[1]}|{user[2]}\n"
        if i + 1 >= limit:
            break
    return text


def format_posters_full(users, limit=500) -> str:
    text = ".|Autore|#OC|Karma OC|Post totali|Karma totali\n"
    text += ":-:|:-:|:-:|:-:|:-:|:-:\n"
    for i, user in enumerate(users):
        text += f"{i + 1}|/u/{user[0]}|{user[1]}|{user[2]:,d}|{user[3]}|{user[4]:,d}\n"
        if i + 1 >= limit:
            break
    return text


def main():
    logging.info("Starting leaderboard...")

    engine = create_engine()
    session_maker = sessionmaker(bind=engine)

    reddit = make_reddit()

    # We will test our reddit connection here
    if not config.TEST and not test_reddit_connection(reddit):
        exit()

    sess = session_maker()

    # query
    top_users = (
        sess.query(
            Investor.name,
            func.coalesce(Investor.balance + func.sum(Investment.amount), Investor.balance).label(
                "networth"
            ),
        )
        .outerjoin(Investment, and_(Investor.name == Investment.name, Investment.done == 0))
        .group_by(Investor.name)
        .order_by(desc("networth"))
        .limit(500)
        .all()
    )
    top_poster = sess.execute(
        """
    SELECT  name,
            SUM(oc) AS coc,
            SUM(CASE OC WHEN 1 THEN final_upvotes ELSE 0 END) AS soc,
            count(*) as ct,
            sum(final_upvotes) as st
    FROM "Buyables"
    WHERE done = 1
    GROUP BY name
    ORDER BY coc DESC, soc DESC
    LIMIT :limit""",
        {"limit": 100},
    ).fetchall()

    # Sidebar
    sidebar_text = f"""
/r/BancaDelMeme è un posto dove si puoi comprare, vendere,
condividere, fare e investire sui meme liberamente.

*****

**Migliori utenti:**

{format_investor(top_users, 10)}

[Classifica completa](/r/BancaDelMeme/wiki/leaderboardbig)


**Migliori autori di OC:**

{format_posters_small(top_poster, 3)}

[Classifica completa](/r/BancaDelMeme/wiki/leaderboardocbig)

Ultimo aggiornamento: {localtime}


###***[Inviaci dei suggerimenti!](https://www.reddit.com/message/compose?to=%2Fr%2FBancaDelMeme)***

&nbsp;

***

**Subreddit ai quali potresti essere interessato:**

/r/italy

***
***
"""

    # redesign
    if not config.TEST:
        for subreddit in config.SUBREDDITS:
            # poster
            for widget in reddit.subreddit(subreddit).widgets.sidebar:
                if isinstance(widget, praw.models.TextArea):
                    if widget.shortName.lower().replace(" ", "") == "top10":
                        widget.mod.update(text=format_investor(top_users, 10))
                        logging.info(" -- Updated redesign top10: %s", subreddit)
                        break
            # investor
            for widget in reddit.subreddit(subreddit).widgets.sidebar:
                if isinstance(widget, praw.models.TextArea):
                    if widget.shortName.lower() == "migliori autori":
                        widget.mod.update(text=format_posters_small(top_poster, 4))
                        logging.info(" -- Updated redesign migliori autori: %s", subreddit)
                        break

    # Old and wiki
    logging.info(" -- Updating sidebar text to:")
    logging.info(sidebar_text.replace("\n", "\\n"))
    if not config.TEST:
        for subreddit in config.SUBREDDITS:
            sub = reddit.subreddit(subreddit)
            # Sidebar update
            sub.mod.update(description=sidebar_text)
            logging.info("Updated sidebar: %s", subreddit)
            # wiki full poster
            wikipage = sub.wiki["leaderboardocbig"]
            wikipage.edit(format_posters_full(top_poster, 100))
            logging.info("Updated wiki poster: %s", subreddit)
            # wiki full investor
            wikipage = sub.wiki["leaderboardbig"]
            wikipage.edit(format_investor(top_users, 500))
            logging.info("Updated wiki investor: %s", subreddit)

    # Report the Reddit API call stats
    rem = int(reddit.auth.limits["remaining"])
    res = int(reddit.auth.limits["reset_timestamp"] - time.time())
    logging.info(" -- API calls remaining: %s, resetting in %.2fs", rem, res)

    sess.close()


if __name__ == "__main__":
    main()
