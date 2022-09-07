import logging
import math
import os
import re
import time
import traceback

import praw
from sqlalchemy import and_, desc, func

import config
import help_info
import message
import utils
from models import Investment, Investor

REDDIT = None

if not config.TEST:
    REDDIT = praw.Reddit(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        username=config.USERNAME,
        password=config.PASSWORD,
        user_agent=config.USER_AGENT,
    )


# Decorator to mark a commands that require a user
# Adds the investor after the comment when it calls the method (see broke)
def req_user(wrapped_function):
    """
    This is a wrapper function that ensures user exists
    """

    def wrapper(self, sess, comment, *args):
        investor = sess.query(Investor).filter(Investor.name == comment.author.name).first()

        if not investor:
            logging.info(" -- autocreating")
            self.create(sess, comment)
            investor = sess.query(Investor).filter(Investor.name == comment.author.name).first()

        return wrapped_function(self, sess, comment, investor, *args)

    return wrapper


# Monkey patch exception handling
def reply_wrap(self, body):
    """
    Wrapper function to make a reddit reply
    """
    logging.info(" -- replying")

    if config.POST_TO_REDDIT:
        try:
            return self.reply(body)
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
            return False
    else:
        logging.info(body)
        return "0"


def edit_wrap(self, body):
    logging.info(" -- editing response")

    if config.POST_TO_REDDIT:
        try:
            return self.edit(body)
        # TODO: get rid of this broad except
        except Exception as e:
            logging.error(e)
            traceback.print_exc()
            return False
    else:
        logging.info(body)
        return False


praw.models.Comment.reply_wrap = reply_wrap
praw.models.Comment.edit_wrap = edit_wrap


class CommentWorker:
    """
    This class is responsible for everything that happens
    in the comment. With some regex rules, it sees all of
    the commands and it has methods to execute on demand
    """

    multipliers = {
        "k": int(1e3),
        "m": int(1e6),
        "b": int(1e9),
        "t": int(1e12),
        "quad": int(1e15),
        # Has to be above q, or regex will stop at q instead of searching for quin/quad
        "quin": int(1e18),
        "q": int(1e15),
        "%": "%",
    }

    # Allowed websites for !template command
    websites = [
        "imgur.com",
        "i.imgur.com",
        "m.imgur.com",
        "reddit.com",
        "i.reddit.com",
        "v.reddit.com",
        "i.redd.it",
        "v.redd.it",
        "i.imgflip.com",
        "i.kym-cdn.com",
    ]
    template_sources = [rf"https://{re.escape(website)}\S+" for website in websites]
    commands = [
        r"!attivi",
        r"!saldo",
        r"!bancarotta",
        r"!create",
        r"!crea",
        r"!aiuto\s*!?(.+)?",
        r"!ignora",
        r"!investi\s+([\d,.]+)\s*(%s)?(?:\s|$)" % "|".join(multipliers),
        r"!invest\s+([\d,.]+)\s*(%s)?(?:\s|$)" % "|".join(multipliers),
        r"!mercato",
        r"!top",
        r"!versione",
        r"!assegna\s+(\S+)\s+(\S+)",
        r"!template\s+(%s)" % "|".join(template_sources),
        r"!template\s+\[(%s)\]\(\1\)" % "|".join(template_sources),
        r"!vendi",
        r"!investitutto",
        r"!rimuovi\s+(\d)",
    ]

    def __init__(self, sm):
        self.regexes = [re.compile(x, re.MULTILINE | re.IGNORECASE) for x in self.commands]
        self.Session = sm

    def __call__(self, comment):
        # Ignore items that aren't Comments (i.e. Submissions)
        # (And skip this check in the tests since we use a mock)
        if not isinstance(comment, praw.models.Comment) | (os.getenv("TEST") != ""):
            return

        # Ignore comments at the root of a Submission
        if comment.is_root:
            return

        # Ignore comments without an author (deleted)
        if not comment.author:
            return

        # Ignore comments older than a threshold
        max_age = 60 * 15  # fifteen minutes
        comment_age = time.time() - int(comment.created_utc)
        if comment_age > max_age:
            return

        # Parse the comment body for a command
        for reg in self.regexes:
            matches = reg.fullmatch(comment.body.strip())
            if not matches:
                continue

            cmd = matches.group()
            attrname = cmd.split(" ")[0][1:].lower()

            if not hasattr(self, attrname):
                continue

            logging.info(" -- %s: %s", comment.author.name, cmd)

            try:
                sess = self.Session()
                getattr(self, attrname)(sess, comment, *matches.groups())
                # TODO: make this except more narrow
            except Exception as e:
                logging.error(e)
                traceback.print_exc()
                sess.rollback()
            else:
                sess.commit()

            sess.close()
            break
        else:
            self._sconosciuto(comment)

    def _sconosciuto(self, comment):
        return comment.reply_wrap(message.cmd_sconosciuto())

    def ignora(self, sess, comment):
        """
        Just ignore function
        """
        pass

    def aiuto(self, sess, comment, command_name=None):
        """
        Returns help information
        """
        if command_name is None:
            return comment.reply_wrap(message.HELP_ORG)

        help_msg = f"COMMAND `!{command_name}`"
        help_msg += help_info.help_dict.get(
            command_name, "Comando non trovato, assicurati di averlo scritto correttamente."
        )
        return comment.reply_wrap(help_msg)

    def mercato(self, sess, comment):
        """
        Return the meme market's current state
        """
        total = sess.query(func.coalesce(func.sum(Investor.balance), 0)).scalar()

        invested, active = (
            sess.query(func.coalesce(func.sum(Investment.amount), 0), func.count(Investment.id))
            .filter(Investment.done == 0)
            .first()
        )

        return comment.reply_wrap(message.modify_market(active, total, invested))

    def top(self, sess, comment):
        """
        Returns the top users in the meme market
        """
        leaders = (
            sess.query(
                Investor.name,
                func.coalesce(
                    Investor.balance + func.sum(Investment.amount), Investor.balance
                ).label("networth"),
            )
            .outerjoin(Investment, and_(Investor.name == Investment.name, Investment.done == 0))
            .group_by(Investor.name)
            .order_by(desc("networth"))
            .limit(5)
            .all()
        )

        return comment.reply_wrap(message.modify_top(leaders))

    def create(self, sess, comment):
        self.crea(sess, comment)

    def crea(self, sess, comment):
        """
        This one is responsible for creating a new user
        """
        author = comment.author.name
        user_exists = sess.query(Investor).filter(Investor.name == author).exists()

        # Let user know they already have an account
        if sess.query(user_exists).scalar():
            return comment.reply_wrap(message.CREATE_EXISTS_ORG)

        # Create new investor account
        sess.add(Investor(name=author))
        # TODO: Make the initial balance a constantconstant
        return comment.reply_wrap(message.modify_create(comment.author, config.STARTING_BALANCE))

    @req_user
    def investi(self, sess, comment, investor, amount, suffix):
        """
        This function invests
        """
        if config.CLOSED:
            return comment.reply_wrap(message.CLOSED_ORG)

        multiplier = CommentWorker.multipliers.get(suffix, 1)

        # Allows input such as '!invest 100%' and '!invest 50%'
        if multiplier == "%":
            amount = int(investor.balance * (int(amount) / 100))
        else:
            try:
                amount = int(amount.replace(",", ""))
                amount = amount * multiplier
            except ValueError:
                return

        # Sets the minimum investment to 1% of an investor's balance or 100 Mc
        minim = int(investor.balance / 100)
        if amount < minim or amount < 100:
            return comment.reply_wrap(message.modify_min_invest(minim))

        author = comment.author.name
        new_balance = investor.balance - amount

        if new_balance < 0:
            return comment.reply_wrap(message.modify_insuff(investor.balance))

        upvotes_now = int(comment.submission.ups)
        # apply 15 minute grace period
        if comment.created_utc - comment.submission.created_utc < 60 * 15:
            upvotes_now = min(upvotes_now, int(math.pow(3, upvotes_now / 5) - 1))
        # 0 upvotes is too strong, so what we do is make around 1 minumum
        if upvotes_now < 1:
            upvotes_now = 1
        deltatime = min(int((comment.created_utc - comment.submission.created_utc) / 60), 60)

        # Sending a confirmation
        response = comment.reply_wrap(message.modify_invest(amount, upvotes_now, new_balance))

        sess.add(
            Investment(
                post=comment.submission.id,
                upvotes=upvotes_now,
                deltatime=deltatime,
                comment=comment.id,
                name=author,
                amount=amount,
                response=response.id,
                done=False,
            )
        )

        investor.balance = new_balance

    def invest(self, *args, **kwargs):
        """
        This function invests
        """
        self.investi(*args, **kwargs)

    @req_user
    def saldo(self, sess, comment, investor):
        """
        Returns user's balance
        """
        return comment.reply_wrap(message.modify_balance(investor.balance, investor.networth(sess)))

    @req_user
    def bancarotta(self, sess, comment, investor):
        """
        Checks if the user is broke. If he is, resets his/her balance to 100 MemeCoins
        """
        if investor.balance >= 100:
            return comment.reply_wrap(message.modify_broke_money(investor.balance))

        active = (
            sess.query(func.count(Investment.id))
            .filter(Investment.done == 0)
            .filter(Investment.name == investor.name)
            .scalar()
        )

        if active > 0:
            return comment.reply_wrap(message.modify_broke_active(active))

        # Indeed, broke
        investor.balance = 100
        investor.broke += 1

        return comment.reply_wrap(message.modify_broke(investor.broke))

    @req_user
    def attivi(self, sess, comment, investor):
        """
        Returns a list of all active investments made by the user
        """
        active_investments = (
            sess.query(Investment)
            .filter(Investment.done == 0)
            .filter(Investment.name == investor.name)
            .order_by(Investment.time)
            .all()
        )

        return comment.reply_wrap(message.modify_active(active_investments))

    def template(self, sess, comment, link):
        """
        OP can submit the template link to the bot's sticky
        """

        # Type of comment is praw.models.reddit.comment.Comment, which
        # does not have a lot of documentation in the docs, for more
        # informationg go to
        # github.com/praw-dev/praw/blob/master/praw/models/reddit/comment.py
        comment.refresh()
        if not comment.is_submitter:
            return comment.reply_wrap(message.TEMPLATE_NOT_OP)

        # Checking if the upper comment is the bot's sticky
        if not comment.parent().stickied:
            return comment.reply_wrap(message.TEMPLATE_NOT_STICKY)

        # What if user spams !template commands?
        if comment.parent().edited:
            return comment.reply_wrap(message.TEMPLATE_ALREADY_DONE)

        # If OP posted a template, replace the hint
        edited_response = message.modify_template_op(link, f"u/{comment.author.name}")
        edited_response += message.INVEST_PLACE_HERE_NO_FEE

        comment.parent().edit_wrap(edited_response)
        return comment.reply_wrap(message.TEMPLATE_SUCCESS)

    def versione(self, sess, comment):
        """
        Return the date when the bot was deployed
        """
        return comment.reply_wrap(message.modify_deploy_version(utils.DEPLOY_DATE))

    @req_user
    def vendi(self, sess, comment, investor):
        """
        Returns a list of all active investments made by the user
        """
        if config.CLOSED:
            return comment.reply_wrap(message.CLOSED_ORG)

        investments = (
            sess.query(Investment)
            .filter(Investment.done == 0)
            .filter(Investment.post == comment.submission.id)
            .filter(Investment.name == investor.name)
            .order_by(Investment.time)
            .all()
        )

        taxes = 0
        for investment in investments:
            if comment.removed_by_category:
                # no taxes on deleted submissions
                remaining = config.INVESTMENT_DURATION - int(time.time()) + investment.time
                tax = min(99, pow(remaining / 60 / 60, 1.5)) / 100  # (1% every hour)^1.5 - max 99%
                taxes += investment.amount - round(investment.amount - investment.amount * tax)
                investment.amount = round(investment.amount - investment.amount * tax)
            # expire investment time (update it in the past)
            investment.time = int(time.time()) - config.INVESTMENT_DURATION

        sess.commit()

        return comment.reply_wrap(message.modify_sell_investment(len(investments), taxes))

    @req_user
    def investitutto(self, sess, comment, investor):
        self.investi(sess, comment, str(investor.balance), None)

    def rimuovi(self, _, comment, rule):
        if not comment.author:
            logging.info(" -- no author")
            return
        if comment.author.name not in config.ADMIN_ACCOUNTS:
            logging.info(" -- not admin")
            return self._sconosciuto(comment)
        extra = None
        try:
            extra = comment.subreddit.rules()['rules'][int(rule)]['violation_reason']
        except:
            pass
        reply = reply_wrap(comment.submission, message.rimozione(rule, extra))
        comment.submission.mod.remove()
        comment.mod.remove()
        if reply and reply != "0":
            reply.mod.lock()
        logging.info(" -- removed post")
