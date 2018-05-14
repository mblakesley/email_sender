#!/usr/bin/python3

import smtplib
from email.message import EmailMessage

from email_sender_config import *

msg = EmailMessage()
msg.set_content(body_text)

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = subject_text
msg['From'] = env_from
msg['To'] = env_to

# Send the message
smtp_session = smtplib.SMTP(host)
smtp_session.set_debuglevel(1)
smtp_session.send_message(msg)
smtp_session.quit()
