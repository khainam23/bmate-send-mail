import imaplib, time, json, re, requests, logging
from email.header import decode_header
from typing import Final
from email import message_from_bytes
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.mongodb import mongodb

# Configure logger
logger = logging.getLogger(__name__)

# ==============================
# Cấu hình
# ==============================
# IMAP_SERVER: Final = settings.HOST_IMAP
# EMAIL_ACCOUNT: Final = settings.EMAIL_ADDRESS
# EMAIL_PASSWORD: Final = settings.EMAIL_PASSWORD_APP
WHERE_READ_EMAIL: str = 'INBOX'
READ_TYPE_EMAIL: str = 'ALL'


class EmailExtract:
    def __init__(self, imap_server, email_account, email_password ,mail, processed_emails, queue_refresh_time):
        self.imap_server = imap_server
        self.email_account = email_account
        self.email_password = email_password
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
    
    def _parse_date_to_timestamp(self, date_value):
        """Convert date (string hoặc int) thành Unix timestamp"""
        if isinstance(date_value, int):
            return date_value
        
        if not isinstance(date_value, str):
            return None
        
        date_str = date_value.strip()
        if not date_str:
            return None
        
        # Thử các định dạng khác nhau
        formats = ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y']
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Convert to timestamp
                timestamp = int(parsed_date.astimezone().timestamp())
                return timestamp
            except ValueError:
                continue
        
        return None
    
    def create_label_if_not_exists(self, label_name="auto_updated"):
        """Tạo label nếu chưa tồn tại"""
        try:
            status, folders = self.mail.list()
            if status == 'OK':
                label_exists = any(label_name.encode() in folder for folder in folders)
                if not label_exists:
                    self.mail.create(label_name)
                    logger.info(f"✅ Đã tạo label: {label_name}")
        except Exception as e:
            logger.warning(f"⚠️ Không thể tạo label: {e}")

    def _add_label_to_email(self, mail_id, label_name="auto_updated"):
        """Gán label cho email đã xử lý"""
        try:
            # Gmail sử dụng X-GM-LABELS
            self.mail.store(mail_id, '+X-GM-LABELS', label_name)
            logger.info(f"✅ Đã gán label '{label_name}' cho email {mail_id.decode()}")
            return True
        except Exception as e:
            logger.error(f"❌ Lỗi khi gán label: {e}")
            return False

    def login(self):
        self.mail = imaplib.IMAP4_SSL(self.imap_server)
        self.mail.login(self.email_account, self.email_password)
        logger.info("✅ Đã đăng nhập IMAP thành công!")
        self.mail.select(WHERE_READ_EMAIL)  # READ-WRITE mode để có thể set Seen

    def _init_queue(self):
        """Khởi tạo hoặc refresh queue"""
        current_time = datetime.now().astimezone()
        
        # Nếu chưa có thời gian refresh hoặc đã quá thời gian
        if self.queue_refresh_time is None or current_time >= self.queue_refresh_time:
            self.processed_emails.clear()
            days_range = 30 # chỉ lưu trong 30 ngày từ ngày chạy dự án
            self.queue_refresh_time = current_time + timedelta(days=days_range)
            logger.info(f"🔄 Queue đã được refresh. Sẽ refresh lại vào: {self.queue_refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Hiển thị thông tin whitelist
            if self.allowed_senders:
                logger.info(f"📋 Whitelist sender: {', '.join(self.allowed_senders)}")
            else:
                logger.info("📋 Whitelist sender: Không giới hạn (cho phép tất cả)")

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
            logger.error("❌ Không lấy được email từ IMAP server.")
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
                # filtered_ids.append(mail_id)

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
            logger.error(f"❌ Không lấy được email {mail_id.decode()}")
            return None, None, None, None, None

        raw_email = data[0][1]
        msg = message_from_bytes(raw_email)

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
                email_date = parsedate_to_datetime(date_header)
                email_date = email_date.astimezone()
            except Exception as e:
                logger.warning(f"⚠️  Không thể parse email date: {e}")
                email_date = None

        # Lấy body HTML
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/html" and "attachment" not in str(part.get("Content-Disposition")):
                    html_body = part.get_payload(decode=True).decode(errors="ignore")

                    # Xoá block <style> ... </style> luôn cả nội dung bên trong
                    html_body = re.sub(r'<style.*?>.*?</style>', '', html_body, flags=re.DOTALL | re.IGNORECASE)

                    # Xoá toàn bộ tag HTML còn lại
                    body = re.sub(r'<[^>]+>', '', html_body).strip()
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
        email_match = re.search(
            r'Email:\s*["\'<\(\[]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})[>"\'\)\],\s]*',
            body,
            re.IGNORECASE
        )

        if email_match:
            extracted_data['email'] = email_match.group(1).strip().lower()
        
        # Trích xuất Phone
        phone_patterns = [
            r'Phone:\s*([^\n\r]+)',
            r'Tel:\s*([^\n\r]+)',
            r'Mobile:\s*([^\n\r]+)',
            r'Contact\s+Number:\s*([^\n\r]+)',
        ]

        extracted_data['phone'] = ""  # mặc định nếu không tìm thấy

        for pattern in phone_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                extracted_data['phone'] = match.group(1).strip()
                break

        if not re.fullmatch(r'[0-9+\-\s()]{5,}', extracted_data['phone']):
            extracted_data['phone'] = ""
        
        # Trích xuất Date (Approximate Move-In Date hoặc các biến thể)
        date_patterns = [
            r'(?:Approximate\s+)?Move-In\s+Date:\s*([^\n\r]+)',
            r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Move\s+In:\s*([^\n\r]+)'
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, body, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1).strip()
                timestamp = self._parse_date_to_timestamp(date_str)
                extracted_data['date'] = timestamp if timestamp else date_str
                break
        
        # Trích xuất Content - sử dụng toàn bộ nội dung email đã được làm sạch
        # Xoá footer của email RealEstateJapan
        body = re.split(r'View all inquiries', body, flags=re.IGNORECASE)[0]
        body = re.split(r'This is a post-only mailing', body, flags=re.IGNORECASE)[0]
        body = re.split(r'Kind regards', body, flags=re.IGNORECASE)[0]

        # Xoá nhiều dòng trống liên tiếp (chỉ để lại 1 dòng)
        body = re.sub(r'\n\s*\n+', '\n', body)

        # Nếu muốn xoá TẤT CẢ dòng trống -> dùng dòng dưới
        body = '\n'.join(line for line in body.splitlines() if line.strip())

        extracted_data['content'] = body.strip()

        
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
            r'Monthly\s+Rent:\s*([^\n\r]+)',
        ]

        extracted_data['budget'] = 0  # mặc định

        for pattern in budget_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                extracted_data['budget'] = match.group(1).strip()
                break

        # Nếu không phải dạng số → đưa về 0
        if not re.fullmatch(r'[0-9.,]+', extracted_data['budget']):
            extracted_data['budget'] = 0
        
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
            from datetime import timezone

            try:
                if email_date.tzinfo is not None:
                    # Nếu có tzinfo, convert về UTC rồi lấy timestamp
                    email_timestamp = int(email_date.astimezone(timezone.utc).timestamp())
                else:
                    # Nếu không có tzinfo (naive datetime)
                    # => gắn local timezone rồi convert về UTC
                    local_dt = email_date.astimezone()  # hệ thống tự chọn tz local
                    email_timestamp = int(local_dt.timestamp())

                extracted_data["contact_date"] = email_timestamp

            except Exception as e:
                logger.warning(f"⚠️ Không thể parse email date: {e}")
                extracted_data["contact_date"] = None

        
        # Kiểm tra xem có đủ TẤT CẢ các trường bắt buộc không
        required_fields = {
            'name': extracted_data['name'],
            'email': extracted_data['email'],
            'contact_date': extracted_data['contact_date'],
            'content': extracted_data['content']
        }
        
        if all(required_fields.values()):
            return extracted_data
        
        # Lưu thông tin các trường thiếu để debug
        extracted_data['_missing_fields'] = [field for field, value in required_fields.items() if not value]
        return None

    def read_and_store(self):
        # Kiểm tra và refresh queue nếu cần
        self._check_and_refresh_queue()
        
        mail_ids = self.list_email_ids(30)
        logger.info(f"📧 Tìm thấy {len(mail_ids)} email(s)")
        logger.info(f"📊 Queue hiện tại: {len(self.processed_emails)} email đã xử lý")
        
        new_emails_count = 0
        store_data = []
        for mail_id in mail_ids:
            # Kiểm tra email đã được xử lý chưa (chỉ theo mail_id)
            if self._is_email_processed(mail_id):
                continue
            
            new_emails_count += 1
            subject, from_, body, msg, email_date = self.fetch_email(mail_id)
            if subject is None:
                continue
            
            # Kiểm tra sender có được phép không
            if not self._is_sender_allowed(from_):
                logger.info(f"🚫 Bỏ qua email từ sender không được phép: {from_}")
                self._mark_email_processed(mail_id)
                continue

            # Kiểm tra xem email này có phải là reply của thread đã xử lý không
            if self._is_email_processed(mail_id, msg):
                self._mark_email_processed(mail_id)
                continue

            extracted_data = self.check_email_format(subject, body, email_date)
            if extracted_data:
                logger.info(f"✅ Email hợp lệ: {extracted_data.get('name')} ({extracted_data.get('email')})")
                self._add_label_to_email(mail_id)
                store_data.append({
                    "email_id": mail_id.decode(),
                    "data": extracted_data,
                    "can_send": True,
                    "created_at": datetime.now()
                })
                time.sleep(0.5)
                
                # Đánh dấu email và thread đã xử lý
                self._mark_email_processed(mail_id, msg)
            else:
                # Email không hợp lệ hoặc thiếu trường bắt buộc
                logger.warning(f"❌ Email không hợp lệ: {subject}")
                
                # Vẫn đánh dấu đã xử lý để không kiểm tra lại
                self._mark_email_processed(mail_id)
        
        logger.info(f"✨ Hoàn thành! Đã tìm thấy {new_emails_count} email mới")
        logger.info("💾 Bắt đầu lưu vào db...")
        self.save_db(store_data)
        
    def save_db(self, store_data):
        collection = mongodb.get_collection(settings.NAME_COLLECTION_MODEL_SEND_MAIL)
      
        if not store_data or len(store_data) == 0:
            logger.info("ℹ️  Không có dữ liệu mới để lưu vào DB")
            return  # tránh insert rỗng
        
        try:
            collection.insert_many(store_data, ordered=False) # import song song có lỗi vẫn làm tiếp
            logger.info(f"✅ Đã lưu {len(store_data)} email vào DB")
        except Exception as e:
            logger.error(f"❌ Lỗi khi lưu vào DB: {e}", exc_info=True)
        
    def call_api(self):
        try:
            session = requests.Session()
            
            # Trước tiên cứ login vào
            response_login = session.post(settings.URL_LOGIN_CRM_BMATE, json={
                "user_username": settings.ACCOUNT_ADMIN,
                "user_password": settings.PASSWORD_ADMIN
            })
            
            if response_login.status_code != 200:
                logger.error(f"❌ Lỗi khi login CRM: Status {response_login.status_code}, Response: {response_login.text[:200]}")
                return False
            
            token = response_login.json().get('token', '')
            
            # Sau đó gọi refresh token
            refresh_token = session.post(settings.URL_REFRESH_TOKEN_CRM_BMATE, json={
               "refresh_token": token
            })
            
            if refresh_token.status_code != 200:
                logger.error(f"❌ Lỗi khi refresh token CRM: Status {refresh_token.status_code}, Response: {refresh_token.text[:200]}")
                return False
            
            access_token = refresh_token.json().get('access_token', '')
            
             # Cuối cùng là gửi mail          
            collection = mongodb.get_collection(settings.NAME_COLLECTION_MODEL_SEND_MAIL)
            
            extracted_data = collection.find_one(
                {"can_send": True},
                sort=[("created_at", -1)]
            )
            
            if not extracted_data or not extracted_data.get("data"):
                logger.info("ℹ️  Không có dữ liệu để gửi API")
                return
            
            _id = extracted_data['_id']
            extracted_data = extracted_data["data"]
            
            logger.info(f"📤 Chuẩn bị gửi dữ liệu đến CRM: {extracted_data.get('name')} - {extracted_data.get('email')}")
            
            url = settings.URL_CALL_CRM_BMATE
            
            # Parse dates to ensure they're timestamps
            contact_date = extracted_data.get('contact_date')
            if isinstance(contact_date, str):
                parsed = self._parse_date_to_timestamp(contact_date)
                contact_date = parsed if parsed else int(datetime.now().timestamp())
            elif contact_date is None:
                contact_date = int(datetime.now().timestamp())
            else:
                contact_date = int(contact_date)
            
            date_field = extracted_data.get('date')
            if isinstance(date_field, str):
                parsed = self._parse_date_to_timestamp(date_field)
                date_field = parsed if parsed else int(datetime.now().timestamp())
            elif date_field is None:
                date_field = int(datetime.now().timestamp())
            else:
                date_field = int(date_field)
            
            json_data = {
                "account_manager": 1,
                "account_name": extracted_data.get('name', ""),
                "account_source": [
                    17
                ],
                "relation_id": 1,
                "country_id": 1,
                "description": extracted_data.get('content', ""),
                "contacts": [
                    {
                        "honorifics": extracted_data.get('name', ""),
                        "first_name": extracted_data.get('name', ""),
                        "title": extracted_data.get('name', ""),
                        "phone_home": extracted_data.get('phone', ""),
                        "email": extracted_data.get('email', ""),
                        "birthdate": None,
                        "gender_id": None,
                        "description": extracted_data.get('content', ""),
                        "email_unsubcribe": 0,
                        "is_primary": 1
                    }
                ],
                "custom_fields": {
                    "ngay_khach_contact": contact_date,
                    "ngay_du_kien_vao_nha": date_field,
                    "ngan_sach_tien_thue": extracted_data.get('budget') or 0,
                    "overseas_dang_o_nhat": extracted_data.get('overseas') or "",
                    "nen_tang_lien_he": [
                        1
                    ],
                    "visa": extracted_data.get('visa') or "",
                    "nuoi_pet": extracted_data.get('pet') or "",
                    "ghi_chu": extracted_data.get('content', "")
                }
            }
            
            print(json.dumps(json_data))
            
            headers = {
                "Authorization": f"{access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0"
            }
            
            response = session.post(url, json=json_data, headers=headers)
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"✅ Gửi API thành công! Response: {response.text[:200]}")
                collection.update_one(
                    {"_id": _id},
                    {"$set": {"can_send": False, "success": "Send success"}}
                )
                return True
            else:
                logger.warning(f"⚠️ API trả về status: {response.status_code}, Response: {response.text[:200]}")
                # Đánh trường can_send là False và thêm trường error nhận được cho nó
                collection.update_one(
                    {"_id": _id},
                    {"$set": {"can_send": False, "error": response.text}}
                )
                return False

        except Exception as e:
            logger.error(f"❌ Lỗi khi gửi API: {str(e)}", exc_info=True)
            try:
                collection.update_one(
                    {"_id": _id},
                    {"$set": {"can_send": False, "error": str(e)}}
                )
            except Exception as db_error:
                logger.error(f"❌ Không thể cập nhật MongoDB: {str(db_error)}", exc_info=True)
                pass
            return False
    
    def logout(self):
        try:
            self.mail.logout()
            logger.info("👋 Đã đăng xuất IMAP")
        except Exception as e:
            logger.error(f"❌ Lỗi khi đăng xuất IMAP: {e}")
        
email_extarct = EmailExtract('', '', '',None, set(), None)


if __name__ == "__main__":
    email_extarct.call_api()