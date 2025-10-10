import imaplib
import email
from email.header import decode_header
from typing import Final
import time
import json
import re
from datetime import datetime, timedelta
from datetime import datetime, timedelta, timezone

from app.core.config import settings

# ==============================
# Cấu hình
# ==============================
IMAP_SERVER: Final = settings.HOST_IMAP
EMAIL_ACCOUNT: Final = settings.EMAIL_ADDRESS
EMAIL_PASSWORD: Final = settings.EMAIL_PASSWORD_APP
WHERE_READ_EMAIL: str = 'INBOX'
READ_TYPE_EMAIL: str = 'ALL'


class EmailExtract:
    def __init__(self, mail, processed_emails, queue_refresh_time):
        self.mail = mail
        self.processed_emails = processed_emails
        self.queue_refresh_time = queue_refresh_time
        self._init_queue()
        
    def login(self):
        self.mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        self.mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        print("Đã đăng nhập thành công!")
        self.mail.select(WHERE_READ_EMAIL)  # READ-WRITE mode để có thể set Seen

    def _init_queue(self):
        """Khởi tạo hoặc refresh queue"""
        current_time = datetime.now().astimezone()
        
        # Nếu chưa có thời gian refresh hoặc đã quá thời gian
        if self.queue_refresh_time is None or current_time >= self.queue_refresh_time:
            self.processed_emails.clear()
            days_range = 30 # chỉ lưu trong 30 ngày từ ngày chạy dự án
            self.queue_refresh_time = current_time + timedelta(days=days_range)
            print(f"🔄 Queue đã được refresh. Sẽ refresh lại vào: {self.queue_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def _check_and_refresh_queue(self):
        """Kiểm tra và refresh queue nếu cần"""
        current_time = datetime.now().astimezone()
        if current_time >= self.queue_refresh_time:
            self._init_queue()

    def _is_email_processed(self, mail_id, msg=None):
        """Kiểm tra email đã được xử lý chưa (bao gồm cả thread)"""
        email_id = mail_id.decode() if isinstance(mail_id, bytes) else mail_id
        
        # Kiểm tra mail_id trước
        if email_id in self.processed_emails:
            return True
        
        # Nếu có msg, kiểm tra thread (Message-ID, In-Reply-To, References)
        if msg:
            # Lấy Message-ID của email hiện tại
            message_id = msg.get("Message-ID", "").strip()
            if message_id and message_id in self.processed_emails:
                return True
            
            # Kiểm tra In-Reply-To (email được reply)
            in_reply_to = msg.get("In-Reply-To", "").strip()
            if in_reply_to and in_reply_to in self.processed_emails:
                return True
            
            # Kiểm tra References (chuỗi thread)
            references = msg.get("References", "").strip()
            if references:
                ref_ids = references.split()
                for ref_id in ref_ids:
                    if ref_id in self.processed_emails:
                        return True
        
        return False

    def _mark_email_processed(self, mail_id, msg=None):
        """Đánh dấu email đã được xử lý (bao gồm cả thread IDs)"""
        email_id = mail_id.decode() if isinstance(mail_id, bytes) else mail_id
        self.processed_emails.add(email_id)
        
        # Nếu có msg, lưu cả Message-ID và thread IDs
        if msg:
            # Lưu Message-ID của email hiện tại
            message_id = msg.get("Message-ID", "").strip()
            if message_id:
                self.processed_emails.add(message_id)
            
            # Lưu In-Reply-To
            in_reply_to = msg.get("In-Reply-To", "").strip()
            if in_reply_to:
                self.processed_emails.add(in_reply_to)
            
            # Lưu References
            references = msg.get("References", "").strip()
            if references:
                ref_ids = references.split()
                self.processed_emails.update(ref_ids)

    def list_email_ids(self, limit=None):
        """Lấy danh sách email theo thời gian và giới hạn số lượng"""
        # Thời gian bắt đầu (N phút trước), local timezone aware
        time_range_minutes = settings.EMAIL_TIME_RANGE_MINUTES
        since_time = (datetime.now().astimezone() - timedelta(minutes=time_range_minutes))  # aware datetime
        
        # Format ngày theo chuẩn IMAP (DD-Mon-YYYY)
        since_date = since_time.strftime("%d-%b-%Y")
        search_criteria = f'({READ_TYPE_EMAIL} SINCE {since_date})'
        
        status, data = self.mail.search(None, search_criteria)
        if status != "OK":
            print("Không lấy được email.")
            return []

        mail_ids = data[0].split()
        filtered_ids = []

        for mail_id in mail_ids:
            status, data = self.mail.fetch(mail_id, '(INTERNALDATE)')
            if status != "OK":
                continue

            date_str = data[0].decode()
            match = re.search(r'INTERNALDATE "([^"]+)"', date_str)
            if not match:
                continue

            email_date_str = match.group(1)
            try:
                # Parse email date từ IMAP (bao gồm timezone)
                email_date = datetime.strptime(email_date_str, "%d-%b-%Y %H:%M:%S %z")
                # Chuyển về local timezone (aware datetime)
                email_date_local = email_date.astimezone()
                
                if email_date_local >= since_time:
                    filtered_ids.append(mail_id)
            except ValueError:
                # Nếu parse lỗi, vẫn giữ email
                filtered_ids.append(mail_id)

        if limit is None:
            return filtered_ids
        return filtered_ids[-limit:]

    def fetch_email(self, mail_id):
        """Lấy email chỉ theo HTML, không mark Seen tự động"""
        status, data = self.mail.fetch(mail_id, '(BODY.PEEK[])')
        if status != "OK":
            print(f"Không lấy được email {mail_id.decode()}")
            return None, None, None, None

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        # Decode sender
        from_ = msg.get("From")

        # Lấy body HTML
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/html" and "attachment" not in str(part.get("Content-Disposition")):
                    html_body = part.get_payload(decode=True).decode(errors="ignore")
                    body = re.sub('<[^<]+?>', '', html_body).strip()
                    break
        else:
            if msg.get_content_type() == "text/html":
                html_body = msg.get_payload(decode=True).decode(errors="ignore")
                body = re.sub('<[^<]+?>', '', html_body).strip()

        return subject, from_, body, msg

    def check_email_format(self, subject, body):
        """
        Kiểm tra và trích xuất các trường bắt buộc từ email:
        - Name (Tên khách hàng) - BẮT BUỘC
        - Email (Email khách hàng) - BẮT BUỘC
        - Date (Ngày dự kiến) - BẮT BUỘC
        - Content/Inquiry (Nội dung yêu cầu) - BẮT BUỘC
        
        Returns:
            dict: Dữ liệu trích xuất nếu hợp lệ (có đủ 4 trường), None nếu không hợp lệ
        """
        if not body.strip():
            return None
        
        # Khởi tạo dict chứa dữ liệu trích xuất
        extracted_data = {
            'name': None,
            'email': None,
            'date': None,
            'content': None
        }
        
        # Trích xuất Name
        name_match = re.search(r'Name:\s*([^\n\r]+)', body, re.IGNORECASE)
        if name_match:
            extracted_data['name'] = name_match.group(1).strip()
        
        # Trích xuất Email
        email_match = re.search(r'Email:\s*([^\s\n\r]+@[^\s\n\r]+)', body, re.IGNORECASE)
        if email_match:
            extracted_data['email'] = email_match.group(1).strip()
        
        # Trích xuất Date (Approximate Move-In Date hoặc các biến thể)
        date_patterns = [
            r'(?:Approximate\s+)?Move-In\s+Date:\s*([^\n\r]+)',
            r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Move\s+In:\s*([^\n\r]+)'
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, body, re.IGNORECASE)
            if date_match:
                extracted_data['date'] = date_match.group(1).strip()
                break
        
        # Trích xuất Content/Inquiry
        inquiry_match = re.search(r'Inquiry:\s*([^\n\r]+)', body, re.IGNORECASE)
        if inquiry_match:
            extracted_data['content'] = inquiry_match.group(1).strip()
        
        # Kiểm tra xem có đủ TẤT CẢ các trường bắt buộc không
        if all([extracted_data['name'], extracted_data['email'], 
                extracted_data['date'], extracted_data['content']]):
            return extracted_data
        
        return None

    def read_and_send_api(self):
        # Kiểm tra và refresh queue nếu cần
        self._check_and_refresh_queue()
        
        mail_ids = self.list_email_ids(30)
        print(f"📧 Tìm thấy {len(mail_ids)} email(s)")
        print(f"📊 Queue hiện tại: {len(self.processed_emails)} email đã xử lý")
        
        new_emails_count = 0
        for mail_id in mail_ids:
            # Kiểm tra email đã được xử lý chưa (chỉ theo mail_id)
            if self._is_email_processed(mail_id):
                print(f"⏭️  Bỏ qua email ID {mail_id.decode()} (đã xử lý)")
                continue
            
            new_emails_count += 1
            subject, from_, body, msg = self.fetch_email(mail_id)
            if subject is None:
                continue

            # Kiểm tra xem email này có phải là reply của thread đã xử lý không
            if self._is_email_processed(mail_id, msg):
                print(f"⏭️  Bỏ qua email '{subject}' (thread đã xử lý - có thể là reply)")
                self._mark_email_processed(mail_id)
                continue

            extracted_data = self.check_email_format(subject, body)
            if extracted_data:
                print("✅ Email hợp lệ - Dữ liệu trích xuất:")
                print(f"  - Tên: {extracted_data['name']}")
                print(f"  - Email: {extracted_data['email']}")
                print(f"  - Ngày: {extracted_data['date']}")
                print(f"  - Nội dung: {extracted_data['content']}")
                print("Bắt đầu gửi API...")
                
                # Đánh dấu email và thread đã xử lý
                self._mark_email_processed(mail_id, msg)
            else:
                # Email không hợp lệ hoặc thiếu trường bắt buộc → giữ unseen
                print(f"❌ Email không hợp lệ hoặc thiếu thông tin bắt buộc: {subject}")
                # Vẫn đánh dấu đã xử lý để không kiểm tra lại
                self._mark_email_processed(mail_id)

            time.sleep(0.5)
        
        print(f"✨ Hoàn thành! Đã xử lý {new_emails_count} email mới")
    def logout(self):
        self.mail.logout()
        
email_extarct = EmailExtract(None, set(), None)