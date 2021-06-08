import argparse
import mimetypes
import random
import smtplib
import string
from email.message import EmailMessage
from pprint import pprint
from typing import List, Optional

from pydantic import BaseModel, FilePath, validator, root_validator


def main() -> None:
    arg_data: dict = parse_args()
    email_data: EmailData = EmailData(**arg_data)
    pprint(email_data.dict(), sort_dicts=False)
    email: EmailMessage = compose_email(email_data)
    # email_data includes envelope data
    send_email(email, email_data, arg_data["verbosity"])


def parse_args() -> dict:
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('-d', metavar='dest-host', help='destination IP/host', dest='destination')
    parser.add_argument('-p', type=int, metavar='dest-port', help='destination port', dest='port')
    parser.add_argument('-f', metavar='envelope-from', help='envelope "from" address', dest='envelope_from')
    parser.add_argument('-F', metavar='header-from', help='header "from" address', dest='header_from')
    parser.add_argument('-t', metavar='envelope-to', help='envelope "to" addresses (comma-separated)', dest='envelope_to')
    parser.add_argument('-T', metavar='header-to', help='header "to" addresses (comma-separated)', dest='header_to')
    parser.add_argument('-s', metavar='subject', help='subject text', dest='subject')
    parser.add_argument('-b', metavar='body', help='body text', dest='body')
    parser.add_argument('-a', metavar='attach', help='attachments (absolute path)', dest='attachments')
    # TODO: update this to match smtplib debug levels
    parser.add_argument('-v', action='store_true', default=False, help='enable verbose output', dest='verbosity')

    return vars(parser.parse_args())


class EmailData(BaseModel):
    """Email data model, for clarity"""
    destination: str
    port: int = 587
    # avoiding EmailStr for envelope info because we want the ability to test weird vals
    envelope_from: Optional[str] = None
    header_from: Optional[str] = None
    envelope_to: Optional[List[str]] = None
    header_to: Optional[List[str]] = None
    # TODO: cc/bcc (header versions? get added to to's?)
    # TODO: headers
    subject: str
    body: str
    # TODO: properly handle '~'
    attachments: List[FilePath] = []

    @validator('envelope_to', 'header_to', 'attachments', pre=True)
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
        if vals.get('envelope_from') is None:
            assert vals.get('header_from') is not None, \
                'either "envelope from" or "header from" must be provided'
            vals['envelope_from'] = cls._parse_addr(vals['header_from'])
        if vals.get('envelope_to') is None:
            assert vals.get('header_to') is not None, \
                'minimally, either "envelope to" or "header to" must be provided'
            vals['envelope_to'] = [cls._parse_addr(hdr_to) for hdr_to in vals['header_to']]
        return vals

    @staticmethod
    def _parse_addr(header: str) -> str:
        return header.split('<')[-1].strip('>')


def compose_email(email_data: EmailData) -> EmailMessage:
    email: EmailMessage = EmailMessage()
    email.set_content(email_data.body)
    email['Subject'] = email_data.subject
    if email_data.header_from is not None:
        email['From'] = email_data.header_from
    if email_data.header_to is not None:
        email['To'] = ', '.join(email_data.header_to)

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

    return email


def send_email(email: EmailMessage, email_data: EmailData, verbosity: bool) -> None:
    smtp_session = smtplib.SMTP(host=email_data.destination, port=email_data.port)
    smtp_session.set_debuglevel(verbosity)
    if verbosity:
        print('')
    try:
        smtp_session.send_message(
            msg=email,
            from_addr=email_data.envelope_from,
            to_addrs=email_data.envelope_to,
        )
    except:
        pass
    smtp_session.quit()
    # TODO: on error, fail gracefully but report error to user!


main()
