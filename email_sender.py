#!/usr/bin/python3

import smtplib
from email.message import EmailMessage

import config

# Compose email
msg = EmailMessage()
msg.set_content(config.body_text)
msg['Subject'] = config.subject_text
msg['From'] = config.env_from
msg['To'] = config.env_to

# Send email
smtp_session = smtplib.SMTP(config.host)
smtp_session.set_debuglevel(1)
smtp_session.send_message(msg)
smtp_session.quit()

# Print summary
print('Imagine a summary here')
