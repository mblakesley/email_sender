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
dest_host = args.d or config.host
subject = args.u or config.subject_text
body = args.b or config.body_text
env_from = args.f or config.env_from
env_to = args.t or config.env_to

# Compose email
email = EmailMessage()
email.set_content(body)
email['Subject'] = subject
email['From'] = env_from
email['To'] = env_to

# Send email
smtp_session = smtplib.SMTP(dest_host)
smtp_session.set_debuglevel(1)
smtp_session.send_message(email)
smtp_session.quit()

# Print summary
print('Imagine a summary here')
