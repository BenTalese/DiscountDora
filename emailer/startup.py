import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from dora_api.infrastructure.logging_setup import configure_logging
from emailer.delivery import send_email
from emailer.product_model import ProductModel
from emailer.user_model import UserModel

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


def startup():
    # D2: log dir derived from the same DORA_DATA_DIR / DORA_LOG_DIR
    # vars as the other two services so a single mount captures
    # everything. Explicit EMAILER_LOG_DIR wins if set.
    import os
    log_dir = os.environ.get("EMAILER_LOG_DIR")
    if log_dir:
        log_dir_path = Path(log_dir).expanduser().resolve()
    else:
        explicit = os.environ.get("DORA_LOG_DIR")
        if explicit:
            log_dir_path = Path(explicit).expanduser().resolve() / "emailer"
        else:
            data_dir = os.environ.get("DORA_DATA_DIR", "data")
            log_dir_path = Path(data_dir).expanduser().resolve() / "logs" / "emailer"
    configure_logging(
        "emailer",
        log_dir_path,
        debug=False,
    )
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
        #                in requests.get("http://127.0.0.1:5170/api/users").json()
        #                if _UserData['send_deals_on_day'] == _DayOfWeekToday]

        # if _Recipients:
        #     _Offers = [ProductModel(**_OfferData)
        #                for _OfferData
        #                in requests.get("http://127.0.0.1:5170/api/webScraper/offers").json()]

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
        logging.getLogger(__name__).exception("An exception occurred:")
        raise e


if __name__ == "__main__":
    startup()
