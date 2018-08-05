#!/usr/bin/python3

import argparse
import smtplib
from email.message import EmailMessage

import config

# Parse command-line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', help='destination IP/host')
parser.add_argument('-f', help='envelope "from" address')
parser.add_argument('-t', help='envelope "to" address')
parser.add_argument('-u', help='subject text')
parser.add_argument('-b', help='body text')
args = parser.parse_args()

# Get vars straight
vars = {
    'dest host': args.d or config.host,
    'env from': args.f or config.env_from,
    'env to': args.t or config.env_to,
    'subject': args.u or config.subject_text,
    'body': args.b or config.body_text,
}

# Process aliases
for k, v in vars.items():
    if v in config.aliases:
        vars[k] = config.aliases[v]

# Compose email
email = EmailMessage()
email.set_content(vars["body"])
email['Subject'] = vars["subject"]
email['From'] = vars["env from"]
email['To'] = vars["env to"]

# Send email
smtp_session = smtplib.SMTP(vars["dest host"])
smtp_session.set_debuglevel(1)
smtp_session.send_message(email)
smtp_session.quit()
