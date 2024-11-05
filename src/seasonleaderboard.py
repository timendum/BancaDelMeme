"""Script to write a txt file with the full leaderboard a the and of a season"""
import logging
import time

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker

import config
import leaderboard
from models import Buyable, Investment, Investor

logging.basicConfig(level=logging.INFO)
localtime = time.strftime("{%Y-%m-%d %H:%M:%S}")

# TODO: add docstring
def main():
    logging.info("Starting leaderboard...")

    engine = create_engine(config.DB, pool_recycle=60, pool_pre_ping=True)
    session_maker = sessionmaker(bind=engine)

    sess = session_maker()

    # check for open Buyable
    buyables = sess.query(Buyable).filter(Buyable.done == 0).all()
    if buyables:
        print(f"Found {len(buyables)} active buyables, stopping")
        return

    # check for open Investment
    investments = sess.query(Investment).filter(Investment.done == 0).all()
    if investments:
        print(f"Found {len(investments)} active investments, stopping")
        return

    logging.info("Checks ok")

    top_users = (
        sess.query(
            Investor.name, func.coalesce(Investor.balance, Investor.balance).label("networth")
        )
        .group_by(Investor.name)
        .order_by(desc("networth"))
        .all()
    )
    logging.info("top_users fetched")

    top_poster = sess.execute(
        """
    SELECT  name,
            SUM(oc) AS coc,
            SUM(CASE OC WHEN 1 THEN final_upvotes ELSE 0 END) AS soc,
            count(*) as ct,
            sum(final_upvotes) as st
    FROM "Buyables"
    WHERE oc <> 0
    GROUP BY name
    ORDER BY st DESC, coc DESC, soc DESC""",
    ).fetchall()
    logging.info("top_poster fetched")

    with open("stagione.txt", "w") as oo:
        oo.write("# Stagione XXX\n\nClassifica definitiva della xxx stagione.\n\n")
        oo.write(leaderboard.format_investor(top_users, 10000))
        oo.write("\n\n\n# Migliori autori di OC\n\n\n")
        oo.write(leaderboard.format_posters_full(top_poster, 1000))

    sess.close()

    logging.info("Done")


if __name__ == "__main__":
    main()
