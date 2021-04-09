import argparse
import random
import smtplib
import string
from email.message import EmailMessage
from pprint import pprint

from pydantic import BaseModel, EmailStr, root_validator, validator


class EmailData(BaseModel):
    destination: str
    port: int = 587
    envelope_from: EmailStr
    header_from: str = ''
    envelope_to: EmailStr
    header_to: str = ''
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

    @root_validator
    def default_headers(cls, values: dict):
        """Default header values to envelope values if needed"""
        if not values.get('header_from'):
            values['header_from'] = values['envelope_from']
        if not values.get('header_to'):
            values['header_to'] = values['envelope_to']
        return values


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

# Display email properties
pprint(email_data.dict(exclude={'verbosity'}), sort_dicts=False)
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
