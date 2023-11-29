import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from clapy import DependencyInjectorServiceProvider

from framework.emailer.get_users_presenter import GetUsersPresenter
from framework.emailer.service_collection_builder import \
    ServiceCollectionBuilder
from interface_adaptors.controllers.user_controller import UserController

sys.path.append(os.getcwd())
from framework.emailer.delivery import send_email

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
logger: logging.Logger

async def startup():
    logger = configure_logger() # TODO: This should be part of service collection (but size of this app might not require it)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(process, 'interval', hours=1)
    scheduler.start()

async def process():
    try:
        _CurrentDirectory = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(_CurrentDirectory, 'appsettings.json'), 'r') as _File:
            SECRETS = json.load(_File)

        _ServiceProvider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()
        _UserController: UserController = _ServiceProvider.get_service(UserController)
        _Presenter = GetUsersPresenter()
        await _UserController.get_users_async(_Presenter)

        _Recipients = []
        for _User in _Presenter.users:
            _DayOfWeekToday = datetime.now().weekday()
            if _User.send_deals_on_day.weekday() == _DayOfWeekToday:
                _Recipients.append(_User.email)

        if _Recipients:
            _Offers = [] # TODO: Get offers, must call API
            send_email(_Offers, SECRETS["SENDER_EMAIL"], SECRETS["SENDER_PASSWORD"], _Recipients)

        send_email([], SECRETS["SENDER_EMAIL"], SECRETS["SENDER_PASSWORD"], ["ben.talese@gmail.com"])

    except Exception:
        logger.exception("An exception occurred: ")

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


if __name__ == "__main__":
    asyncio.run(startup())
