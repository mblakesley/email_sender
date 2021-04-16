import argparse
import mimetypes
import random
import smtplib
import string
from email.message import EmailMessage
from pprint import pprint
from typing import List

from pydantic import BaseModel, EmailStr, FilePath, root_validator, validator


parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
parser.add_argument('-d', metavar='dest-host', help='destination IP/host', dest='destination')
parser.add_argument('-p', type=int, metavar='dest-port', help='destination port', dest='port')
parser.add_argument('-f', metavar='envelope-from', help='envelope "from" address', dest='envelope_from')
# parser.add_argument('-F', metavar='header-from', help='header "from" address', dest='header from')
parser.add_argument('-t', metavar='envelope-to', help='envelope "to" address', dest='envelope_to')
# parser.add_argument('-T', metavar='header-to', help='header "to" address', dest='header to')
parser.add_argument('-u', metavar='subject', help='subject text', dest='subject')
parser.add_argument('-b', metavar='body', help='body text', dest='body')
# TODO: attachments arg
# TODO: update this to match smtplib debug levels
parser.add_argument('-v', action='store_true', help='enable verbose output', dest='verbosity')


class EmailData(BaseModel):
    destination: str
    port: int = 587
    envelope_from: str = ''  # can be illegit if you want
    header_from: str = ''
    # TODO: list of to's - need to come in as comma-separated strings
    envelope_to: EmailStr
    header_to: str = ''
    # TODO: cc/bcc (header versions? get added to to's?)
    # TODO: headers
    subject: str = ''
    body: str = ''
    # TODO: properly handle '~'
    attachments: List[FilePath] = []
    verbosity: bool = False

    @root_validator
    def default_headers(cls, values: dict):
        """Default header values to envelope values if needed"""
        if not values.get('header_from'):
            values['header_from'] = values['envelope_from']
        if not values.get('header_to'):
            values['header_to'] = values['envelope_to']
        return values

    @validator('subject')
    def append_id(cls, subject: str) -> str:
        """Append alphanum ID to subject"""
        length: int = 5
        alphanum: str = string.digits + string.ascii_letters
        ids: list = [random.choice(alphanum) for _ in range(length)]
        return '{} {}'.format(subject, ''.join(ids))


email_data: EmailData = EmailData(**vars(parser.parse_args()))

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

# TODO: move to data model
# process attachments
for path in email_data.attachments:
    # "encoding" is only used to help determine content type
    ctype, encoding = mimetypes.guess_type(str(path))
    if ctype is None or encoding is not None:
        # No guess or file is encoded (compressed), so use a generic "bag-of-bits" type
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    with open(str(path), 'rb') as file:
        email.add_attachment(file.read(), maintype=maintype, subtype=subtype, filename=path.name)

# Send email
smtp_session = smtplib.SMTP(host=email_data.destination, port=email_data.port)
smtp_session.set_debuglevel(email_data.verbosity)
smtp_session.send_message(
    msg=email,
    from_addr=email_data.envelope_from,
    to_addrs=email_data.envelope_to,
)
smtp_session.quit()
