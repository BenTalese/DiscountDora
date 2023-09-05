from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, ssl
import random
import os

from .generate import generate_email_body
from framework.web_scraper.types import ProductOffers



def send_email(
        product_offers: ProductOffers,
        sender_user: str,
        sender_password: str,
        receivers: List[str]) -> None:

    port = 587
    smtp_server = "smtp.gmail.com"
    context = ssl.create_default_context()
    message = prepare_email(product_offers)

    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_user, sender_password)
        for recipient in receivers:
            server.sendmail(sender_user, recipient, message)



def prepare_email(product_offers: ProductOffers) -> str:
    text_body = "Oops, you should use an email client that supports HTML rendering to view this email."
    html_body = generate_email_body(product_offers)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, 'food_emojis.txt'), 'r') as file:
        food_emojis = file.read().split()
    random_food_emoji = random.choice(food_emojis)

    message = MIMEMultipart('alternative')
    message['Subject'] = f"Discount Dora: {random_food_emoji} Weekly Price Report!"
    message.attach(MIMEText(text_body, 'plain'))
    message.attach(MIMEText(html_body, 'html'))

    return message.as_string()
