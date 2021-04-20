import argparse
import mimetypes
import random
import smtplib
import string
from email.message import EmailMessage
from pprint import pprint
from typing import List, Optional

from pydantic import BaseModel, EmailStr, FilePath, validator, root_validator

parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
parser.add_argument('-d', metavar='dest-host', help='destination IP/host', dest='destination')
parser.add_argument('-p', type=int, metavar='dest-port', help='destination port', dest='port')
parser.add_argument('-f', metavar='envelope-from', help='envelope "from" address', dest='envelope_from')
parser.add_argument('-F', metavar='header-from', help='header "from" address', dest='header_from')
parser.add_argument('-t', metavar='envelope-to', help='envelope "to" address', dest='envelope_to')
parser.add_argument('-T', metavar='header-to', help='header "to" address', dest='header_to')
parser.add_argument('-s', metavar='subject', help='subject text', dest='subject')
parser.add_argument('-b', metavar='body', help='body text', dest='body')
parser.add_argument('-a', metavar='attach', help='attachments (absolute path)', dest='attachments')
# TODO: update this to match smtplib debug levels
parser.add_argument('-v', action='store_true', help='enable verbose output', dest='verbosity')


class EmailData(BaseModel):
    """Validation model for email data"""
    destination: str
    port: int = 587
    # avoiding EmailStr for envelope info because we want the ability to test weird vals
    envelope_from: Optional[str] = None
    header_from: Optional[str] = None
    # TODO: list of to's - need to come in as comma-separated strings
    envelope_to: Optional[str] = None
    header_to: Optional[str] = None
    # TODO: cc/bcc (header versions? get added to to's?)
    # TODO: headers
    subject: str
    body: str
    # TODO: properly handle '~'
    attachments: List[FilePath] = []
    verbosity: bool = False

    @validator('attachments', pre=True)
    def str_to_list(cls, var: str) -> List[str]:
        return [s.strip() for s in var.split(',')]

    @validator('subject')
    def append_id(cls, subject: str) -> str:
        """Append alphanum ID to subject"""
        length: int = 5
        alphanum: str = string.digits + string.ascii_letters
        ids: list = [random.choice(alphanum) for _ in range(length)]
        return '{} {}'.format(subject, ''.join(ids))

    @root_validator
    def manage_froms_tos(cls, vals: dict):
        if vals.get("envelope_from") is None:
            assert vals.get("header_from") is not None, \
                'either "envelope from" or "header from" must be provided'
            vals["envelope_from"] = vals["header_from"].split('<')[-1].strip('>')
        if vals.get("envelope_to") is None:
            assert vals.get("header_to") is not None, \
                'either "envelope to" or "header to" must be provided'
            vals["envelope_to"] = vals["header_to"].split('<')[-1].strip('>')
        return vals


email_data: EmailData = EmailData(**vars(parser.parse_args()))

# Display email properties
pprint(email_data.dict(exclude={'verbosity'}), sort_dicts=False)
if email_data.verbosity:
    print('')

# Compose email
email: EmailMessage = EmailMessage()
email.set_content(email_data.body)
email['Subject'] = email_data.subject
if email_data.header_from is not None:
    email['From'] = email_data.header_from
if email_data.header_to is not None:
    email['To'] = email_data.header_to

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
try:
    smtp_session.send_message(
        msg=email,
        from_addr=email_data.envelope_from,
        to_addrs=email_data.envelope_to,
    )
except:
    pass
smtp_session.quit()
# TODO: display error after quitting
