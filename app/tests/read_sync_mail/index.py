# python -m app.tests.read_sync_mail.index

from app.jobs.read_sync_mail.index import EmailExtract

email_extract = EmailExtract()

email_extract.read_and_send_api()

email_extract.logout()