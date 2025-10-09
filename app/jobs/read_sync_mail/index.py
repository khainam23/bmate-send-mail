import imaplib
from app.core.config import settings

# python -m app.jobs.read_sync_mail.index

# ==============================
# Cấu hình
# ==============================
IMAP_SERVER = settings.HOST_IMAP
EMAIL_ACCOUNT = settings.EMAIL_ADDRESS
EMAIL_PASSWORD = settings.EMAIL_PASSWORD_APP

# ==============================
# Xử lý
# ==============================
def name_folders():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    print("Đã đăng nhập thành công!")

    status, folders = mail.list()
    if status == 'OK':
        for f in folders:
            print(f)
    mail.logout()