import imaplib
import email
from email.header import decode_header
from typing import Final

from app.core.config import settings

# python -m app.jobs.read_sync_mail.index

# ==============================
# Cấu hình
# ==============================
IMAP_SERVER: Final = settings.HOST_IMAP
EMAIL_ACCOUNT: Final = settings.EMAIL_ADDRESS
EMAIL_PASSWORD: Final = settings.EMAIL_PASSWORD_APP
WHERE_READ_EMAIL: str = 'INBOX'
READ_TYPE_EMAIL: str = 'UNSEEN'

class EmailExtract:
    def __init__(self):
        self.mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        self.mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        print("Đã đăng nhập thành công!")

        # Chọn hộp thư INBOX
        self.mail.select(WHERE_READ_EMAIL)

    def list_email_ids(self, limit=None):
        status, data = self.mail.search(None, READ_TYPE_EMAIL)
        if status != "OK":
            print("Không lấy được email.")
            return []

        mail_ids = data[0].split()

        if limit is None:  
            # Lấy tất cả
            return mail_ids
        else:              
            # Lấy N email mới nhất
            return mail_ids[-limit:]
    
    def fetch_email(self, mail_id):
        """
        Lấy thông tin email theo mail_id.
        Trả về: subject(str), from_(str), body(str)
        """
        status, data = self.mail.fetch(mail_id, "(RFC822)")
        if status != "OK":
            print(f"Không lấy được email {mail_id.decode()}")
            return None, None, None

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        # Decode sender
        from_ = msg.get("From")

        # Lấy nội dung body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        return subject, from_, body
    
    def read_and_send_api(self):
        mail_ids = self.list_email_ids()
        for mail_id in mail_ids:
            subject, from_, body = self.fetch_email(mail_id)
            if subject is None:
                continue

            print(f"From: {from_}\nSubject: {subject}\nBody: {body[:100]}...\n")

            if(subject.startswith('Cảnh báo')):
                print("Bắt đầu gửi API...")
            else:
                self.mail.store(mail_id, '-FLAGS', '\\Seen')
            
    
    def logout(self):
        self.mail.logout()