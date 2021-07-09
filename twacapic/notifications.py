from pathlib import Path

import yagmail
import yaml
from loguru import logger


def send_mail(recipient, subject, content):

    try:

        with open(Path.cwd() / 'gmail_creds.yaml') as file:
            creds = yaml.safe_load(file)

        yag = yagmail.SMTP(creds['gmail_user'], creds['gmail_password'])
        yag.send(recipient, subject, content)
        logger.info(f'Email sent to {recipient}.\nSubject: {subject}\n{content}')

    except Exception as e:

        logger.error(f'Sending mail failed: {e}')
