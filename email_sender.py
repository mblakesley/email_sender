#!/usr/bin/python3

import argparse
import random
import smtplib
import string
from email.message import EmailMessage

import config


def generate_id(length):
    alphanum = string.digits + string.ascii_letters
    id_list = [random.choice(alphanum) for _ in range(length)]
    return ''.join(id_list)


# Parse command-line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', metavar='host', help='destination IP/host')
parser.add_argument('-f', metavar='email_address', help='envelope "from" address')
parser.add_argument('-t', metavar='email_address', help='envelope "to" address')
parser.add_argument('-u', metavar='string', help='subject text')
parser.add_argument('-b', metavar='string', help='body text')
args = parser.parse_args()

# Get vars straight
email_vars = {
    'dest host': args.d or config.host,
    'env from': args.f or config.env_from,
    'env to': args.t or config.env_to,
    'subject': args.u or config.subject_text,
    'body': args.b or config.body_text,
    'id': generate_id(5),
}
email_vars['subject'] += ' ' + email_vars['id']

# Process aliases
for k, v in email_vars.items():
    if v in config.aliases:
        email_vars[k] = config.aliases[v]

# Compose email
email = EmailMessage()
email.set_content(email_vars['body'])
email['Subject'] = email_vars['subject']
email['From'] = email_vars['env from']
email['To'] = email_vars['env to']

# Send email
smtp_session = smtplib.SMTP(email_vars['dest host'])
smtp_session.set_debuglevel(1)
smtp_session.send_message(email)
smtp_session.quit()
