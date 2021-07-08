from pathlib import Path
from loguru import logger

import yagmail
try:
    import gmail_creds
except ModuleNotFoundError:
    logger.warning('No credentials found for Gmail. No notifications will be sent.')


def send_mail(recipient, subject, content):

    try:
        yag = yagmail.SMTP(gmail_creds.gmail_user, gmail_creds.gmail_password)
        yag.send(recipient, subject, content)
        logger.info(f'Email sent to {recipient}.\nSubject: {subject}\n{content}')
    except Exception as e:
        logger.error(f'Sending mail failed: {e}')
