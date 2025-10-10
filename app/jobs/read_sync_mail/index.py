import imaplib
import email
from email.header import decode_header
from typing import Final
import time
import json
import re
from datetime import datetime, timedelta
from datetime import datetime, timedelta, timezone
import requests

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
        self.allowed_senders = self._parse_allowed_senders()
        self._init_queue()
    
    def _parse_allowed_senders(self):
        """Parse danh sách sender được phép từ config"""
        allowed = settings.ALLOWED_SENDERS.strip()
        if not allowed:
            return None  # None = cho phép tất cả
        # Tách theo dấu phẩy và loại bỏ khoảng trắng, chuyển về lowercase
        return [email.strip().lower() for email in allowed.split(',') if email.strip()]
    
    def _is_sender_allowed(self, from_email):
        """Kiểm tra sender có trong whitelist không"""
        if self.allowed_senders is None:
            return True  # Cho phép tất cả nếu không có whitelist
        
        if not from_email:
            return False
        
        # Trích xuất email từ chuỗi "Name <email@domain.com>" hoặc "email@domain.com"
        email_match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', from_email)
        if not email_match:
            return False
        
        sender_email = (email_match.group(1) or email_match.group(2)).strip().lower()
        return sender_email in self.allowed_senders
        
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
            
            # Hiển thị thông tin whitelist
            if self.allowed_senders:
                print(f"📋 Whitelist sender: {', '.join(self.allowed_senders)}")
            else:
                print("📋 Whitelist sender: Không giới hạn (cho phép tất cả)")

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
            return None, None, None, None, None

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        # Decode sender
        from_ = msg.get("From")
        
        # Lấy ngày nhận email (Date header)
        email_date = None
        date_header = msg.get("Date")
        if date_header:
            try:
                # Parse email date từ header
                from email.utils import parsedate_to_datetime
                email_datetime = parsedate_to_datetime(date_header)
                # Chuyển về local timezone và format theo định dạng mong muốn
                email_date = email_datetime.astimezone().strftime("%d-%m-%Y")
            except Exception as e:
                print(f"⚠️  Không thể parse email date: {e}")
                email_date = None

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

        return subject, from_, body, msg, email_date

    def check_email_format(self, subject, body, email_date=None):
        if not body.strip():
            return None
        
        # Khởi tạo dict chứa dữ liệu trích xuất
        extracted_data = {
            'name': None,
            'email': None,
            'date': None,
            'content': None,
            'phone': None,
            'visa': None,
            'budget': None,
            'overseas': None,
            'pet': None,
            'contact_platform': None,
            'contact_date': None
        }
        
        # Trích xuất Name (đảm bảo không match "Building name:" hoặc các trường khác)
        name_match = re.search(r'^[ \t]*Name:\s*([^\n\r]+)', body, re.IGNORECASE | re.MULTILINE)
        if name_match:
            extracted_data['name'] = name_match.group(1).strip()
        
        # Trích xuất Email
        email_match = re.search(r'Email:\s*([^\s\n\r]+@[^\s\n\r]+)', body, re.IGNORECASE)
        if email_match:
            extracted_data['email'] = email_match.group(1).strip()
        
        # Trích xuất Phone
        phone_patterns = [
            r'Phone:\s*([^\n\r]+)',
            r'Tel:\s*([^\n\r]+)',
            r'Mobile:\s*([^\n\r]+)',
            r'Contact\s+Number:\s*([^\n\r]+)'
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, body, re.IGNORECASE)
            if phone_match:
                extracted_data['phone'] = phone_match.group(1).strip()
                break
        
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
        
        # Trích xuất Visa
        visa_patterns = [
            r'Visa:\s*([^\n\r]+)',
            r'Visa\s+Type:\s*([^\n\r]+)',
            r'Visa\s+Status:\s*([^\n\r]+)'
        ]
        for pattern in visa_patterns:
            visa_match = re.search(pattern, body, re.IGNORECASE)
            if visa_match:
                extracted_data['visa'] = visa_match.group(1).strip()
                break
        
        # Trích xuất Budget (Ngân sách tiền thuê)
        budget_patterns = [
            r'Budget:\s*([^\n\r]+)',
            r'Rental\s+Budget:\s*([^\n\r]+)',
            r'Price\s+Range:\s*([^\n\r]+)',
            r'Monthly\s+Rent:\s*([^\n\r]+)'
        ]
        for pattern in budget_patterns:
            budget_match = re.search(pattern, body, re.IGNORECASE)
            if budget_match:
                extracted_data['budget'] = budget_match.group(1).strip()
                break
        
        # Trích xuất Overseas (Đang ở nước ngoài/Nhật)
        overseas_patterns = [
            r'Overseas:\s*([^\n\r]+)',
            r'Currently\s+in\s+Japan:\s*([^\n\r]+)',
            r'Location:\s*([^\n\r]+)'
        ]
        for pattern in overseas_patterns:
            overseas_match = re.search(pattern, body, re.IGNORECASE)
            if overseas_match:
                extracted_data['overseas'] = overseas_match.group(1).strip()
                break
        
        # Trích xuất Pet
        pet_patterns = [
            r'Pet:\s*([^\n\r]+)',
            r'Pets:\s*([^\n\r]+)',
            r'Have\s+Pet:\s*([^\n\r]+)'
        ]
        for pattern in pet_patterns:
            pet_match = re.search(pattern, body, re.IGNORECASE)
            if pet_match:
                extracted_data['pet'] = pet_match.group(1).strip()
                break
        
        # Trích xuất Contact Platform (Nền tảng liên hệ)
        platform_patterns = [
            r'Contact\s+Platform:\s*([^\n\r]+)',
            r'Platform:\s*([^\n\r]+)',
            r'Source:\s*([^\n\r]+)'
        ]
        for pattern in platform_patterns:
            platform_match = re.search(pattern, body, re.IGNORECASE)
            if platform_match:
                extracted_data['contact_platform'] = platform_match.group(1).strip()
                break
        
        # Trích xuất Contact Date (Ngày khách contact)
        # Ngày khách liên lạc lấy theo ngày nhận được email
        if email_date:
            extracted_data['contact_date'] = email_date
        
        # Kiểm tra xem có đủ TẤT CẢ các trường bắt buộc không
        required_fields = {
            'name': extracted_data['name'],
            'phone': extracted_data['phone'],
            'email': extracted_data['email'],
            'contact_date': extracted_data['contact_date'],
            'content': extracted_data['content']
        }
        
        if all(required_fields.values()):
            return extracted_data
        
        # Lưu thông tin các trường thiếu để debug
        extracted_data['_missing_fields'] = [field for field, value in required_fields.items() if not value]
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
            subject, from_, body, msg, email_date = self.fetch_email(mail_id)
            if subject is None:
                continue
            
            # Kiểm tra sender có được phép không
            if not self._is_sender_allowed(from_):
                print(f"🚫 Bỏ qua email từ sender không được phép: {from_}")
                self._mark_email_processed(mail_id)
                continue

            # Kiểm tra xem email này có phải là reply của thread đã xử lý không
            if self._is_email_processed(mail_id, msg):
                print(f"⏭️  Bỏ qua email '{subject}' (thread đã xử lý - có thể là reply)")
                self._mark_email_processed(mail_id)
                continue

            extracted_data = self.check_email_format(subject, body, email_date)
            if extracted_data:
                print("✅ Email hợp lệ - Dữ liệu trích xuất:")
                print(f"  - Tên: {extracted_data['name']}")
                print(f"  - Email: {extracted_data['email']}")
                print(f"  - Ngày dự kiến: {extracted_data['date']}")
                print(f"  - Nội dung: {extracted_data['content']}")
                
                # In các trường tùy chọn nếu có
                if extracted_data.get('phone'):
                    print(f"  - Số điện thoại: {extracted_data['phone']}")
                if extracted_data.get('visa'):
                    print(f"  - Visa: {extracted_data['visa']}")
                if extracted_data.get('budget'):
                    print(f"  - Ngân sách: {extracted_data['budget']}")
                if extracted_data.get('overseas'):
                    print(f"  - Đang ở nước ngoài: {extracted_data['overseas']}")
                if extracted_data.get('pet'):
                    print(f"  - Nuôi pet: {extracted_data['pet']}")
                if extracted_data.get('contact_platform'):
                    print(f"  - Nền tảng liên hệ: {extracted_data['contact_platform']}")
                if extracted_data.get('contact_date'):
                    print(f"  - Ngày contact: {extracted_data['contact_date']}")
                
                print("Bắt đầu gửi API...")
                self.call_api(extracted_data)
                time.sleep(0.5)
                
                # Đánh dấu email và thread đã xử lý
                self._mark_email_processed(mail_id, msg)
            else:
                # Email không hợp lệ hoặc thiếu trường bắt buộc → giữ unseen
                print(f"\n❌ Email không hợp lệ: {subject}")
                print(f"   📧 From: {from_}")
                
                # Hiển thị thông tin debug về các trường bị thiếu
                if extracted_data is None:
                    print("   ⚠️  Body email trống hoặc không có dữ liệu")
                else:
                    missing_fields = extracted_data.get('_missing_fields', [])
                    if missing_fields:
                        print(f"   ⚠️  Thiếu các trường bắt buộc: {', '.join(missing_fields)}")
                    
                    # Hiển thị các trường đã trích xuất được
                    print("   📋 Các trường đã trích xuất:")
                    print(f"      - Name: {extracted_data.get('name') or '❌ THIẾU'}")
                    print(f"      - Email: {extracted_data.get('email') or '❌ THIẾU'}")
                    print(f"      - Phone: {extracted_data.get('phone') or '❌ THIẾU'}")
                    print(f"      - Contact Date: {extracted_data.get('contact_date') or '❌ THIẾU'}")
                    print(f"      - Content: {extracted_data.get('content') or '❌ THIẾU'}")
                    
                    # Hiển thị body để debug
                    if settings.DEBUG:
                        # Chế độ DEBUG: hiển thị toàn bộ body
                        print(f"   📄 Full Body (DEBUG mode):")
                        print(f"      {body}")
                    else:
                        # Chế độ thường: chỉ hiển thị 300 ký tự đầu
                        preview_length = min(300, len(body))
                        print(f"   📄 Body preview ({preview_length} ký tự đầu):")
                        print(f"      {body[:preview_length]}{'...' if len(body) > preview_length else ''}")
                
                # Vẫn đánh dấu đã xử lý để không kiểm tra lại
                self._mark_email_processed(mail_id)
        
        print(f"✨ Hoàn thành! Đã xử lý {new_emails_count} email mới")
        
    def call_api(self, extracted_data):
        try:
            url = settings.URL_CALL_CRM_BMATE
            
            json_data = {
                "user_id": 0,
                "recipient": None,
                "token_api": "",
                "opportunity_status": None,
                "opp_type_source": "https://bmate.getflycrm.com",
                "opp_source_content": "http://127.0.0.1",
                "account_type": [],
                "key": settings.KEY_CALL_CRM_BMATE,
                "opp_url_source": "http://127.0.0.1:5500/index.html",
                "account_name": extracted_data.get('name', ""),
                "account_description": extracted_data.get('content', ""),
                "account_email": extracted_data.get('email', ""),
                "account_phone": extracted_data.get('phone', ""),
                "custom_fields": {
                    "ngay_khach_contact": extracted_data.get('contact_date', ""),
                    "visa": extracted_data.get('visa', ""),
                    "ngay_du_kien_vao_nha": extracted_data.get('date', ""),
                    "ngan_sach_tien_thue": extracted_data.get('budget', ""),
                    "overseas_dang_o_nhat": extracted_data.get('overseas', ""),
                    "nuoi_pet": extracted_data.get('pet', ""),
                    "nen_tang_lien_he": extracted_data.get('contact_platform', "")
                },
                "utm_params": {
                    "utm_source": "",
                    "utm_campaign": "",
                    "utm_medium": "",
                    "utm_content": "",
                    "utm_term": "",
                    "utm_user": "",
                    "utm_account": "",
                    "sources": "http://127.0.0.1:5500/index.html"
                }
            }
            
            data_form = {
                "data_form": json.dumps(json_data),
                "verify_with_google_recaptcha": False
            }
            
            response = requests.post(url, json=data_form)
            
            if response.status_code == 200:
                print(f"✅ Gửi API thành công! Response: {response.text[:200]}")
                return True
            else:
                print(f"⚠️ API trả về status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi khi gọi API: {str(e)}")
            return False
    
    
    def logout(self):
        self.mail.logout()
        
email_extarct = EmailExtract(None, set(), None)