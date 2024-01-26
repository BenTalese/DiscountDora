import os
import sys
from uuid import uuid4

sys.path.append(os.getcwd())

import asyncio
import json
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from framework.emailer.delivery import send_email
from framework.emailer.product_model import ProductModel
from framework.emailer.user_model import UserModel

'''
TODO:
    - Store system email into database (hmm...can't do this with the app password though, may need to prompt for it and store it hashed)
        - Could stay in appsettings?
        - Could prompt for it in front end?
        - System email is not a user, you cannot "log in" with it
    - Prompt for email registration in front end, save to DB
    - Figure out where email schedule preferences should be stored, feels slightly weird being with user...just slightly though

    - Filter to users needing emailing
    - If there are any users requiring an email to be sent:
        - Get current offers (invoke scraper directly, not through API)
        - Send email with current offers to all recipients
'''

def configure_logger() -> logging.Logger:
    log_folder = os.path.join(os.path.dirname(__file__), "logs")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    logger = logging.getLogger(__name__)
    log_filename = os.path.join(log_folder, "emailer_logs.txt")
    file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=30)
    file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(lineno)04d | %(message)s'))
    logger.setLevel(logging.INFO) # TODO: appsettings
    logger.addHandler(file_handler)

    return logger

logger: logging.Logger = configure_logger()

def startup():
    asyncio.run(process())
    # logger = configure_logger() # TODO: This should be part of service collection (but size of this app might not require it)
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(process, 'interval', hours=1)
    # scheduler.start()
    # asyncio.get_event_loop().run_forever()

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_forever()

async def process():
    # print("Emailing")
    try:
        _CurrentDirectory = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(_CurrentDirectory, 'appsettings.json'), 'r') as _File:
            SECRETS = json.load(_File)

        _DayOfWeekToday = datetime.now().weekday()

        # _Recipients = [UserModel(**_UserData).email
        #                for _UserData
        #                in requests.get("http://127.0.0.1:5000/api/users").json()
        #                if _UserData['send_deals_on_day'] == _DayOfWeekToday]

        # if _Recipients:
        #     _Offers = [ProductModel(**_OfferData)
        #                for _OfferData
        #                in requests.get("http://127.0.0.1:5000/api/webScraper/offers").json()]

            # TODO: at the minimum, need to send in stock items against the products so they can be grouped by stock item
            # At some point will need shopping list information too

            # send_email(_Offers, SECRETS["SENDER_EMAIL"], SECRETS["SENDER_PASSWORD"], _Recipients)

        send_email([ProductModel(
            "Cadbury",
            None,
            True,
            uuid4(),
            869235,
            "Chocolate Thing",
            5.5,
            7.8,
            uuid4(),
            "g",
            150,
            "https://www.woolworths.com.au/shop/productdetails/869235"
        )],
        SECRETS["SENDER_EMAIL"], SECRETS["SENDER_PASSWORD"], ["ben.talese@gmail.com"])

    except Exception as e:
        logger.exception("An exception occurred:")
        raise e


if __name__ == "__main__":
    startup()
