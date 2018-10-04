#!/usr/bin/python3

import argparse
import random
import smtplib
import string
from email.message import EmailMessage

import config


def generate_id(length):
    """Generate alphanum ID string of specified length"""
    alphanum = string.digits + string.ascii_letters
    id_list = [random.choice(alphanum) for _ in range(length)]
    return ''.join(id_list)


# Parse command-line args
# Note: we do several things to convert the parsed args into a dict formatted to our liking:
# (1) specify key names with `dest=`, (2) convert to dict using `vars()`, (3) remove items with "None" values
parser = argparse.ArgumentParser()
parser.add_argument('-d', metavar='host', help='destination IP/host', dest='host')
parser.add_argument('-f', metavar='email_address', help='envelope "from" address', dest='envelope from')
parser.add_argument('-F', metavar='email_address', help='header "from" address', dest='header from')
parser.add_argument('-t', metavar='email_address', help='envelope "to" address', dest='envelope to')
parser.add_argument('-T', metavar='email_address', help='header "to" address', dest='header to')
parser.add_argument('-u', metavar='string', help='subject text', dest='subject')
parser.add_argument('-b', metavar='string', help='body text', dest='body')
args_dict = vars(parser.parse_args())
args_dict = {k: v for k, v in args_dict.items() if v is not None}

# Get vars straight
email_dict = config.defaults
email_dict.update(args_dict)
email_dict['id'] = generate_id(5)
email_dict.setdefault('header from', email_dict['envelope from'])
email_dict.setdefault('header to', email_dict['envelope to'])
email_dict['subject'] += ' ' + email_dict['id']

# Process aliases
for k, v in email_dict.items():
    if v in config.aliases:
        email_dict[k] = config.aliases[v]

# Compose email
email = EmailMessage()
email.set_content(email_dict['body'])
email['Subject'] = email_dict['subject']
email['From'] = email_dict['header from']
email['To'] = email_dict['header to']

# Send email
smtp_session = smtplib.SMTP(email_dict['host'])
smtp_session.set_debuglevel(1)
smtp_session.send_message(
    email,
    email_dict['envelope from'],
    email_dict['envelope to'],
)
smtp_session.quit()
