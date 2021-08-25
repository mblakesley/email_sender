import argparse
import mimetypes
import random
import smtplib
import string
from email.message import EmailMessage
from pprint import pprint
from typing import Optional

from pydantic import BaseModel, EmailStr, FilePath, validator, root_validator


def main() -> None:
    arg_data: dict = parse_args()
    email_data: EmailData = EmailData(**arg_data)
    pprint(email_data.dict(exclude_none=True, exclude={"verbosity"}), sort_dicts=False)
    email: EmailMessage = compose_email_obj(email_data)
    # email_data includes envelope data
    send_email(email, email_data)


def parse_args() -> dict:
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    # TODO: mandatory args should be indicated in "-h" prompt
    parser.add_argument('-d', metavar='destination', help='destination IP/host', dest='destination')
    parser.add_argument('-p', type=int, metavar='port', help='port', dest='port')
    parser.add_argument('-f', metavar='envelope-from', help='envelope "from" address', dest='envelope_from')
    parser.add_argument('-F', metavar='header-from', help='header "from" address', dest='header_from')
    parser.add_argument('-t', metavar='envelope-to', help='envelope "to" addresses (comma-separated)', dest='envelope_to')
    parser.add_argument('-T', metavar='header-to', help='header "to" addresses (comma-separated)', dest='header_to')
    parser.add_argument('-C', metavar='cc', help='header CC addresses (comma-separated)', dest='header_cc')
    parser.add_argument('-B', metavar='bcc', help='BCC addresses (comma-separated)', dest='bcc')
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
    envelope_from: Optional[str]
    header_from: Optional[str]
    envelope_to: list[str] = []
    header_to: list[str] = []
    header_cc: list[str] = []
    bcc: list[EmailStr] = []
    # TODO: headers
    # TODO: auto-add date & message ID headers
    subject: str
    # TODO: html and/or plaintext content
    body: str
    # TODO: properly handle '~'
    attachments: list[FilePath] = []
    verbosity: bool

    @validator('envelope_to', 'header_to', 'header_cc', 'bcc', 'attachments', pre=True)
    def str_to_list(cls, var: str) -> list[str]:
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
        # smtplib can do most of this, but we do it all ourselves for output clarity
        if vals.get('envelope_from') is None:
            assert vals.get('header_from') is not None, \
                'either "envelope from" or "header from" must be provided'
            # this script treats header from's/to's as the source of truth,
            # since they can accept either low- or high-level formats
            vals['envelope_from'] = cls._parse_addr(vals['header_from'])
        if not vals.get('envelope_to'):
            assert vals.get('header_to'), \
                'minimally, either "envelope to" or "header to" must be provided'
            # design decision: show cc's as both cc's AND env to's (keep bcc separate)
            hdr_rcpts: list[str] = vals.get('header_to') + vals.get('header_cc')
            vals['envelope_to'] = [cls._parse_addr(hdr_rcpt) for hdr_rcpt in hdr_rcpts]
        return vals

    @staticmethod
    def _parse_addr(header: str) -> str:
        return header.split('<')[-1].strip('>')


def compose_email_obj(email_data: EmailData) -> EmailMessage:
    email: EmailMessage = EmailMessage()
    email.set_content(email_data.body)
    email['Subject'] = email_data.subject
    if email_data.header_from is not None:
        email['From'] = email_data.header_from
    if email_data.header_to:
        email['To'] = ', '.join(email_data.header_to)
    if email_data.header_cc:
        email['Cc'] = ', '.join(email_data.header_cc)

    # process attachments
    for path in email_data.attachments:
        # "encoding" is only used to help determine content type
        ctype, encoding = mimetypes.guess_type(str(path))
        if ctype is None or encoding is not None:
            # No guess or file is encoded (compressed), so use a generic "bag-of-bits" type
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with open(str(path), 'rb') as file:
            email.add_attachment(
                file.read(), maintype=maintype, subtype=subtype, filename=path.name
            )

    return email


def send_email(email: EmailMessage, email_data: EmailData) -> None:
    smtp_session = smtplib.SMTP(host=email_data.destination, port=email_data.port)
    smtp_session.set_debuglevel(email_data.verbosity)
    if email_data.verbosity:
        print('')
    try:
        smtp_session.send_message(
            msg=email,
            from_addr=email_data.envelope_from,
            to_addrs=email_data.envelope_to + email_data.bcc,
        )
    # TODO: on error, fail gracefully AND REPORT ERROR TO USER!
    finally:
        smtp_session.quit()

main()
