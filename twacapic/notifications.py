from pathlib import Path
from loguru import logger

import yagmail


def send_mail(recipient, subject, content):

    try:
        yag = yagmail.SMTP(oauth2_file=Path.cwd()/'gmail_creds.json')
        yag.send(recipient, subject, content)
        logger.info(f'Email sent to {recipient}.\nSubject: {subject}\n{content}')
    except Exception as e:
        logger.error(f'Sending mail failed: {e}')
