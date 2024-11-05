# TODO: add docstrin here
import logging

from sqlalchemy.orm import sessionmaker

from models import Buyable, Investment, Investor
from stopwatch import Stopwatch
from utils import create_engine

logging.basicConfig(level=logging.INFO)


def reset_all():
    logging.info("Preparing for new season...")

    engine = create_engine()
    session_maker = sessionmaker(bind=engine)
    stopwatch = Stopwatch()

    logging.info("Reset investors...")
    stopwatch.measure()
    sess = session_maker()
    investors = sess.query(Investor).delete(synchronize_session=False)
    sess.commit()
    duration = stopwatch.measure()
    logging.info("Removed %d investors -- processed in %.2fs", investors, duration)
    sess.close()

    logging.info("Reset investments...")
    stopwatch.measure()
    sess = session_maker()
    investments = sess.query(Investment).delete(synchronize_session=False)
    sess.commit()
    duration = stopwatch.measure()
    logging.info("Removed %d investments -- processed in %.2fs", investments, duration)
    sess.close()

    logging.info("Reset posts...")
    stopwatch.measure()
    sess = session_maker()
    buyables = sess.query(Buyable).delete(synchronize_session=False)
    sess.commit()
    duration = stopwatch.measure()
    logging.info("Removed %d posts -- processed in %.2fs", buyables, duration)
    sess.close()

    logging.info("Clean up...")
    stopwatch.measure()
    sess = session_maker()
    sess.execute("VACUUM")
    sess.commit()
    duration = stopwatch.measure()
    logging.info("-- processed in %.2fs", duration)
    sess.close()


if __name__ == "__main__":
    reset_all()
