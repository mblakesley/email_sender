import argparse
import random
import smtplib
import string
from email.message import EmailMessage

from pydantic import BaseModel, EmailStr, validator


class EmailData(BaseModel):
    destination: str
    port: int = 587
    envelope_from: EmailStr
    header_from: str = ""
    envelope_to: EmailStr
    header_to: str = ""
    subject: str
    body: str
    verbosity: bool = False

    @validator('subject')
    def append_id(cls, subject: str) -> str:
        """Append alphanum ID to subject"""
        length: int = 5
        alphanum: str = string.digits + string.ascii_letters
        ids: list = [random.choice(alphanum) for _ in range(length)]
        return '{} {}'.format(subject, ''.join(ids))

    @validator('header_from', always=True)
    def check_header_from(cls, header_from: str, values: dict):
        return header_from if header_from else values['envelope_from']

    @validator('header_to', always=True)
    def check_header_to(cls, header_to: str, values: dict):
        return header_to if header_to else values['envelope_to']

#
# # Process config
# email_dict = config.defaults
#
# # Process command-line args
# # Note: we do several things to convert the parsed args into a dict formatted to our liking:
# # (1) specify key names with `dest=`, (2) convert to dict using `vars()`, (3) remove items with "None" values
# parser = argparse.ArgumentParser()
# parser.add_argument('-d', metavar='dest-host', help='destination IP/host', dest='host')
# parser.add_argument('-p', type=int, metavar='dest-port', help='destination port', dest='port')
# parser.add_argument('-f', metavar='envelope-from', help='envelope "from" address', dest='envelope from')
# parser.add_argument('-F', metavar='header-from', help='header "from" address', dest='header from')
# parser.add_argument('-t', metavar='envelope-to', help='envelope "to" address', dest='envelope to')
# parser.add_argument('-T', metavar='header-to', help='header "to" address', dest='header to')
# parser.add_argument('-u', metavar='subject', help='subject text', dest='subject')
# parser.add_argument('-b', metavar='body', help='body text', dest='body')
# # TODO: update this to match smtplib debug levels
# parser.add_argument('-v', action='store_true', help='enable verbose output', dest='verbosity')
# args_dict = vars(parser.parse_args())
# args_dict = {k: v for k, v in args_dict.items() if v is not None}
# email_dict.update(args_dict)
#
# # Process aliases
# for k, v in email_dict.items():
#     if v in config.aliases:
#         email_dict[k] = config.aliases[v]

# Display email properties
display_order = ['destination', 'port', 'envelope_from', 'header_from', 'envelope_to', 'header_to', 'subject', 'body']
max_key_len = len(max(email_data.dict(), key=len))
for key in display_order:
    val = getattr(email_data, key, None)
    if val:
        print('{0:{1}} {2}'.format(key +':', max_key_len + 1, val))
if email_data.verbosity:
    print('')

# Compose email
email: EmailMessage = EmailMessage()
email.set_content(email_data.body)
email['Subject'] = email_data.subject
email['From'] = email_data.header_from
email['To'] = email_data.header_to

# Send email
smtp_session = smtplib.SMTP(host=email_data.destination, port=email_data.port)
smtp_session.set_debuglevel(email_data.verbosity)
smtp_session.send_message(
    msg=email,
    from_addr=email_data.envelope_from,
    to_addrs=email_data.envelope_to,
)
smtp_session.quit()
