"""
sqlalchemy is the way we connect to our MySQL database
"""
from sqlalchemy import BigInteger, Boolean, Column, Index, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles

import config


class unix_timestamp(expression.FunctionElement):
    type = Integer()


@compiles(unix_timestamp)
def compile(element, compiler, **kw):
    if 'sqlite://' in config.DB:
        # sqlite 
        return "(strftime('%s', 'now'))"
    # mariadb
    return "unix_timestamp()"


Base = declarative_base()


class Investment(Base):
    """
    Our mighty investments have these columns
    """
    __tablename__ = "Investments"

    id = Column(Integer, primary_key=True)
    post = Column(String(11), nullable=False)
    upvotes = Column(Integer, default=0)
    comment = Column(String(11), nullable=False, unique=True)
    name = Column(String(20), nullable=False, index=True)
    amount = Column(BigInteger, default=100)
    time = Column(Integer, server_default=unix_timestamp())
    done = Column(Boolean, default=False, nullable=False, index=True)
    response = Column(String(11))
    final_upvotes = Column(Integer)
    success = Column(Boolean, default=False)
    profit = Column(BigInteger, default=0)
    firm_tax = Column(Integer, default=0)

    __table_args__ = (Index("ix_Investments_name_done", "name", "done"), )

    def __str__(self):
        return (
            "Investment(" + ", ".join(["{}={!r}".format(k, v) for k, v in self.__dict__.items()]) + ")"
        )

class Investor(Base):
    """
    Our dear investors have these columns
    """
    __tablename__ = "Investors"

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False, unique=True)
    balance = Column(BigInteger, default=config.STARTING_BALANCE)
    completed = Column(Integer, default=0)
    broke = Column(Integer, default=0)
    badges = Column(String(1024), default="[]")
    firm = Column(Integer, default=0)
    firm_role = Column(String(32), default="")

    def networth(self, sess):
        """Return the balance plus all invested amounts (if any)"""
        return self.balance + (sess.query(func.sum(Investment.amount)).filter(
            Investment.name == self.name).filter(Investment.done == 0).first()[0] or 0)

    def __str__(self):
        return (
            "Investor(" + ", ".join(["{}={!r}".format(k, v) for k, v in self.__dict__.items()]) + ")"
        )

class Firm(Base):
    __tablename__ = "Firms"

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False, unique=True)
    balance = Column(BigInteger, default=1000)
    size = Column(Integer, default=0)
    ceo = Column(String(20), nullable=False, default='')
    coo = Column(String(20), nullable=False, default='')
    cfo = Column(String(20), nullable=False, default='')
    execs = Column(Integer, default=0)
    assocs = Column(Integer, default=0)
    tax = Column(Integer, default=15)
    rank = Column(Integer, default=0)
    private = Column(Boolean, default=False)
    last_payout = Column(Integer, server_default=unix_timestamp())


class Invite(Base):
    __tablename__ = "Invites"

    id = Column(Integer, primary_key=True)
    firm = Column(Integer)
    investor = Column(Integer)

class Buyable(Base):
    __tablename__ = "Buyables"

    id = Column(Integer, primary_key=True)
    post = Column(String(11), nullable=False)
    time = Column(Integer, server_default=unix_timestamp())
    response = Column(String(20))
    oc = Column(Integer, default=False, nullable=False)
    done = Column(Boolean, default=False, nullable=False, index=True)
    name = Column(String(20), nullable=False, index=True)
    final_upvotes = Column(Integer)
    profit = Column(BigInteger, default=0)

    def __str__(self):
        return (
            "Buyable(" + ", ".join(["{}={!r}".format(k, v) for k, v in self.__dict__.items()]) + ")"
        )