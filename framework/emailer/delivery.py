import json
import os
import random
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

# from framework.web_scraper.types import ProductOffers

from .generate import generate_email_body, generate_html, heml_test, mjml_test

# TODO: Add requirements mjml or heml (npm install -g mjml)

def send_email(
        product_offers,
        sender_user: str,
        sender_password: str,
        recipients: List[str]) -> None:

    context = ssl.create_default_context()
    message = prepare_email(product_offers)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_user, sender_password)
        for recipient in recipients:
            server.sendmail(sender_user, recipient, message)


def prepare_email(product_offers) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, 'food_emojis.txt'), 'r') as file:
        food_emojis = file.read().split()

    message = MIMEMultipart('alternative')
    message['Subject'] = f"Discount Dora: {random.choice(food_emojis)} Weekly Price Report!"
    # body = MIMEText(generate_email_body(product_offers), 'html')
    body = MIMEText(mjml_test(), 'html')
    message.attach(body)

    return message.as_string()
