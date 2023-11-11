from datetime import datetime
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

sys.path.append(os.getcwd())
from framework.emailer.delivery import send_email

'''
TODO:
    - Service collection
    - Add users to domain
    - Add users to database
    - Add user dto
    - Seed my email into database
    - Add "get users" use case
    - Call "get users" use case from emailer
    - Figure out where email schedule preferences should be stored, feels slightly weird being with user...just slightly though

    - Filter to users needing emailing
    - If there are any users requiring an email to be sent:
        - Get current offers (invoke scraper directly, not through API)
        - Send email with current offers to all recipients
'''
logger: logging.Logger

def startup():
    logger = configure_logger() # TODO: This should be part of service collection (but size of this app might not require it)
    scheduler = BlockingScheduler()
    scheduler.add_job(process, 'interval', hours=1)
    scheduler.start()

def process():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, 'appsettings.json'), 'r') as file:
            SECRETS = json.load(file)

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

if __name__ == '__main__':
    startup()
