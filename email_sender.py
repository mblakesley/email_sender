import mimetypes
import random
import smtplib
import string
from argparse import ArgumentParser, Namespace
from email.message import EmailMessage
from email.utils import make_msgid
from pprint import pprint


# note: the str args that we split into arrays are indicated by "(comma-separated)" in the help args below
parser = ArgumentParser()
parser.add_argument('-d', metavar='destination', help='destination IP/host', dest='destination', required=True)
parser.add_argument('-p', type=int, metavar='port', help='port', dest='port', default=587)
parser.add_argument('-f', metavar='envelope-from', help='envelope "from" address', dest='envelope_from')
parser.add_argument('-F', metavar='header-from', help='header "from" address', dest='header_from', default='')
parser.add_argument('-t', metavar='envelope-to', help='envelope "to" addresses (comma-separated)', dest='envelope_to')
parser.add_argument('-T', metavar='header-to', help='header "to" addresses (comma-separated)', dest='header_to')
parser.add_argument('-C', metavar='cc', help='header CC addresses (comma-separated)', dest='header_cc')
parser.add_argument('-B', metavar='bcc', help='BCC addresses (comma-separated)', dest='bcc')
parser.add_argument('-s', metavar='subject', help='subject text', dest='subject', default='')
parser.add_argument('-b', metavar='body', help='body text', dest='body', default='')
parser.add_argument('-a', metavar='attachments', help='attachments (absolute path) (comma-separated)', dest='attachments')
# TODO: update this to match smtplib debug levels
parser.add_argument('-v', action='store_true', default=False, help='enable verbose output', dest='verbosity')

email_data: Namespace = parser.parse_args()

# split potential CSV strings - they can be empty, 1 value, or CSV
for attr in ('envelope_to', 'header_to', 'header_cc', 'bcc', 'attachments'):
    csv_str: str = getattr(email_data, attr)
    tup_str: tuple = tuple(s.strip() for s in csv_str.split(',')) if csv_str else tuple()
    setattr(email_data, attr, tup_str)


def parse_email_header(email_str: str) -> str:
    return email_str.split('<')[-1].strip('>')


# process & check from's & to's
# smtplib can do most of this, but we do it here for output clarity
# TODO: ensure logic makes sense, then properly note that this script treats header from/to/etc as the source of truth
if email_data.envelope_from is None:
    assert email_data.header_from is not None, 'either "envelope from" or "header from" must be provided'
    # probably want to make this optional at some point
    email_data.envelope_from = parse_email_header(email_data.header_from)
if not email_data.envelope_to:
    if not email_data.header_to:
        parser.error('either "envelope from" or "header from" must be provided')
    assert email_data.header_to, 'either "envelope to" or "header to" must be provided'
    hdr_rcpts: tuple = email_data.header_to + email_data.header_cc
    email_data.envelope_to = tuple(parse_email_header(hdr_rcpt) for hdr_rcpt in hdr_rcpts)

# append alphanum ID to subject
length: int = 5
alphanum: str = string.digits + string.ascii_letters
email_id: str = ''.join([random.choice(alphanum) for _ in range(length)])
email_data.subject += f' {email_id}'

# TODO: headers
# TODO: auto-add date headers
# TODO: html and/or plaintext content
# TODO: for attachments, handle '~' when not interpolated by shell


# print summary
keys_to_exclude = ('verbosity',)
print_data: dict = {k: v for k, v in vars(email_data).items() if k not in keys_to_exclude and v is not None}
pprint(print_data, sort_dicts=False)


# compose email object, i.e., the letter that goes in the envelope
email: EmailMessage = EmailMessage()
if email_data.header_from is not None:
    email['From'] = email_data.header_from
    email['Message-ID'] = make_msgid(domain=email_data.header_from.split('@')[-1])
if email_data.header_to:
    email['To'] = ', '.join(email_data.header_to)
if email_data.header_cc:
    email['Cc'] = ', '.join(email_data.header_cc)
email['Subject'] = email_data.subject
email.set_content(email_data.body)

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


# send email
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
