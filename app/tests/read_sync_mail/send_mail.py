
import smtplib
import random
import time
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings

# --- Cấu hình người gửi và người nhận ---
sender_email = settings.EMAIL_ADDRESS_2
receiver_email = settings.EMAIL_ADDRESS_2
password = settings.EMAIL_PASSWORD_APP_2  # dùng App Password nếu là Gmail


def generate_random_phone():
    """Tạo số điện thoại ngẫu nhiên theo format 8180XXXXXXXX"""
    return f"8180{random.randint(1000, 9999)}{random.randint(1000, 9999)}"


def generate_inquiry_email(name, phone, property_id, property_type, building_name, unit_number, property_url):
    """Tạo HTML template cho email inquiry"""
    random = str(uuid.uuid4())[:8]
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ background-color: #1e1e1e; color: #ddd; font-family: Arial, sans-serif; padding: 20px; }}
    .container {{ background-color: #2c2c2c; padding: 20px; border-radius: 8px; width: 600px; margin: auto; }}
    h2 {{ color: #9bcb48; }}
    * {{color: white;}}
    a {{ color: #52a8ff; text-decoration: none; }}
    .section {{ margin-bottom: 20px; }}
    .label {{ font-weight: bold; color: #fff; }}
  </style>
</head>
<body>
  <div class="container">
    <h2><img src="https://realestate.co.jp/favicon.ico" alt="logo" style="vertical-align:middle;margin-right:10px;">realestatejapan</h2>
    <p>The following is an inquiry lead from Real Estate Japan. Please respond to the client as soon as possible.</p>
    
    <div class="section">
      <p class="label">Property details:</p>
      <p>Property link: <a href="{property_url}">{property_url}</a><br>
         Property ID: {property_id}<br>
         Property Type: {property_type}<br>
         Building name: {building_name}<br>
         Unit number: {unit_number}
      </p>
    </div>

    <div class="section">
      <p class="label">Customer details:</p>
      <p>Name: {name}<br>
         Email: <a href="mailto:dev.test@bmate.com">'dev{random}.test@bmate.com'</a><br>
         Phone: {generate_random_phone()}<br>
         Approximate Move-In Date: 01/05/2026<br>
         Inquiry: This is test
      </p>
    </div>

    <p>View all inquiries in your <a href="https://realestate.co.jp">realestate.co.jp</a> account</p>
    <p>Please click <a href="#">here</a></p>

    <p>Kind regards,<br>
    Real Estate Japan</p>
  </div>
</body>
</html>
"""


# --- Static HTML Templates (không cần UUID/phone ngẫu nhiên) ---
html2 = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      background-color: #1e1e1e;
      color: #ddd;
      font-family: Arial, sans-serif;
      padding: 20px;
    }
    .container {
      background-color: #2c2c2c;
      padding: 20px;
      border-radius: 8px;
      width: 600px;
      margin: auto;
    }
    * {
      color: white;
    }
    h2 {
      color: #9bcb48;
    }
    a {
      color: #52a8ff;
      text-decoration: none;
    }
    p {
      line-height: 1.6;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>
      <img src="https://realestate.co.jp/favicon.ico" alt="logo"
           style="vertical-align:middle;margin-right:10px;">
      realestatejapan
    </h2>

    <p>You have property listings that are set to expire in three days. 
    You will have to renew them if you wish to keep them listed.</p>

    <p>To renew the listings, click on the link below for the corresponding property type. 
    You can then click on any property that you wish to extend the listing for, 
    update any necessary data, and click “Save and Publish” to renew it.</p>

    <p><strong>For Rent: 17 Items</strong><br>
    <a href="https://realestate.co.jp/property/en/forrent?expires_on=2025-10-12&status=online">
      https://realestate.co.jp/property/en/forrent?expires_on=2025-10-12&status=online
    </a></p>

    <p><strong>For Sale: 0 Items</strong><br>
    <a href="https://realestate.co.jp/property/en/forsale?expires_on=2025-10-12&status=online">
      https://realestate.co.jp/property/en/forsale?expires_on=2025-10-12&status=online
    </a></p>

    <p>Thank you for using our service and keeping your property information up to date.</p>

    <p>Kind regards,<br>
    Real Estate Japan</p>
  </div>
</body>
</html>
"""

html4 = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      background-color: #1e1e1e;
      color: #ddd;
      font-family: Arial, sans-serif;
      padding: 20px;
    }
    .container {
      background-color: #2c2c2c;
      padding: 20px;
      border-radius: 8px;
      width: 600px;
      margin: auto;
      border: 2px solid #ff6b6b;
    }
    * {
      color: white;
    }
    h2 {
      color: #ff6b6b;
    }
    a {
      color: #52a8ff;
      text-decoration: none;
    }
    p {
      line-height: 1.6;
    }
    .urgent {
      background-color: #ff6b6b;
      padding: 10px;
      border-radius: 5px;
      font-weight: bold;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>
      <img src="https://realestate.co.jp/favicon.ico" alt="logo"
           style="vertical-align:middle;margin-right:10px;">
      realestatejapan
    </h2>

    <div class="urgent">⚠️ URGENT: Listings Expire Tomorrow!</div>

    <p>Your property listings will expire in <strong>ONE DAY</strong>. 
    Please renew them immediately to keep them listed.</p>

    <p>To renew the listings, click on the link below for the corresponding property type. 
    You can then click on any property that you wish to extend the listing for, 
    update any necessary data, and click "Save and Publish" to renew it.</p>

    <p><strong>For Rent: 5 Items</strong><br>
    <a href="https://realestate.co.jp/property/en/forrent?expires_on=2025-10-10&status=online">
      https://realestate.co.jp/property/en/forrent?expires_on=2025-10-10&status=online
    </a></p>

    <p><strong>For Sale: 3 Items</strong><br>
    <a href="https://realestate.co.jp/property/en/forsale?expires_on=2025-10-10&status=online">
      https://realestate.co.jp/property/en/forsale?expires_on=2025-10-10&status=online
    </a></p>

    <p>Thank you for using our service and keeping your property information up to date.</p>

    <p>Kind regards,<br>
    Real Estate Japan</p>
  </div>
</body>
</html>
"""

html6 = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      background-color: #1e1e1e;
      color: #ddd;
      font-family: Arial, sans-serif;
      padding: 20px;
    }
    .container {
      background-color: #2c2c2c;
      padding: 20px;
      border-radius: 8px;
      width: 600px;
      margin: auto;
    }
    * {
      color: white;
    }
    h2 {
      color: #9bcb48;
    }
    a {
      color: #52a8ff;
      text-decoration: none;
    }
    p {
      line-height: 1.6;
    }
    .summary-box {
      background-color: #3a3a3a;
      padding: 15px;
      border-radius: 5px;
      margin: 15px 0;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>
      <img src="https://realestate.co.jp/favicon.ico" alt="logo"
           style="vertical-align:middle;margin-right:10px;">
      realestatejapan
    </h2>

    <p>This is your weekly summary of property listings expiring in the next 7 days.</p>

    <div class="summary-box">
      <p><strong>Expiring in 1 day:</strong><br>
      For Rent: 2 Items | For Sale: 1 Item</p>
      
      <p><strong>Expiring in 3 days:</strong><br>
      For Rent: 8 Items | For Sale: 4 Items</p>
      
      <p><strong>Expiring in 7 days:</strong><br>
      For Rent: 12 Items | For Sale: 6 Items</p>
    </div>

    <p>To renew your listings, please visit:</p>

    <p><strong>For Rent Properties:</strong><br>
    <a href="https://realestate.co.jp/property/en/forrent?status=online">
      https://realestate.co.jp/property/en/forrent?status=online
    </a></p>

    <p><strong>For Sale Properties:</strong><br>
    <a href="https://realestate.co.jp/property/en/forsale?status=online">
      https://realestate.co.jp/property/en/forsale?status=online
    </a></p>

    <p>Thank you for using our service and keeping your property information up to date.</p>

    <p>Kind regards,<br>
    Real Estate Japan</p>
  </div>
</body>
</html>
"""

html8 = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      background-color: #1e1e1e;
      color: #ddd;
      font-family: Arial, sans-serif;
      padding: 20px;
    }
    .container {
      background-color: #2c2c2c;
      padding: 20px;
      border-radius: 8px;
      width: 600px;
      margin: auto;
      border: 2px solid #9bcb48;
    }
    * {
      color: white;
    }
    h2 {
      color: #9bcb48;
    }
    a {
      color: #52a8ff;
      text-decoration: none;
    }
    p {
      line-height: 1.6;
    }
    .success {
      background-color: #9bcb48;
      padding: 10px;
      border-radius: 5px;
      font-weight: bold;
      text-align: center;
      color: #1e1e1e;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>
      <img src="https://realestate.co.jp/favicon.ico" alt="logo"
           style="vertical-align:middle;margin-right:10px;">
      realestatejapan
    </h2>

    <div class="success">✅ All Your Listings Are Up to Date!</div>

    <p>Good news! You currently have no property listings expiring in the next 7 days.</p>

    <p>All your properties are active and will remain listed. We'll notify you when any listings are approaching their expiration date.</p>

    <p><strong>Current Active Listings:</strong><br>
    For Rent: 25 Items<br>
    For Sale: 15 Items</p>

    <p>To view or manage your listings, please visit:</p>

    <p><a href="https://realestate.co.jp/property/en/forrent?status=online">
      View For Rent Properties
    </a></p>

    <p><a href="https://realestate.co.jp/property/en/forsale?status=online">
      View For Sale Properties
    </a></p>

    <p>Thank you for using our service and keeping your property information up to date.</p>

    <p>Kind regards,<br>
    Real Estate Japan</p>
  </div>
</body>
</html>
"""

# --- Danh sách các template và subject tương ứng ---
# Tạo danh sách email templates động với UUID và số điện thoại ngẫu nhiên
email_templates = []

# Thêm các template inquiry với thông tin ngẫu nhiên
inquiry_properties = [
    {
        "property_id": "1280512",
        "property_type": "For Rent",
        "building_name": "Ka F+style Hagoromo Building No. 5",
        "unit_number": "202",
        "property_url": "https://realestate.co.jp/en/rent/view/1280512"
    },
    {
        "property_id": "2345678",
        "property_type": "For Sale",
        "building_name": "Tokyo Tower Mansion",
        "unit_number": "1505",
        "property_url": "https://realestate.co.jp/en/sale/view/2345678"
    },
    {
        "property_id": "3456789",
        "property_type": "For Rent",
        "building_name": "Shibuya Heights Apartment",
        "unit_number": "801",
        "property_url": "https://realestate.co.jp/en/rent/view/3456789"
    },
    {
        "property_id": "4567890",
        "property_type": "For Rent",
        "building_name": "Roppongi Hills Residence",
        "unit_number": "2103",
        "property_url": "https://realestate.co.jp/en/rent/view/4567890"
    }
]

# Tạo inquiry emails với UUID và số điện thoại ngẫu nhiên
for prop in inquiry_properties:
    unique_id = str(uuid.uuid4())[:8]
    name = f"Dev Test - {unique_id}"
    phone = generate_random_phone()
    
    email_templates.append({
        "subject": "New Inquiry Lead from Real Estate Japan",
        "html": generate_inquiry_email(
            name=name,
            phone=phone,
            property_id=prop["property_id"],
            property_type=prop["property_type"],
            building_name=prop["building_name"],
            unit_number=prop["unit_number"],
            property_url=prop["property_url"]
        )
    })

# Thêm các template khác (expiration notices, summaries)
email_templates.extend([
    {
        "subject": "Property Listings Expiring Soon - Action Required",
        "html": html2
    },
    {
        "subject": "⚠️ URGENT: Property Listings Expire Tomorrow!",
        "html": html4
    },
    {
        "subject": "Weekly Property Expiration Summary",
        "html": html6
    },
    {
        "subject": "✅ All Your Property Listings Are Up to Date",
        "html": html8
    }
])


def send_random_emails(count=1, delay=2):
    """
    Gửi email ngẫu nhiên từ danh sách templates
    
    Args:
        count (int): Số lượng email muốn gửi
        delay (int): Thời gian chờ giữa các email (giây)
    """
    print(f"🚀 Bắt đầu gửi {count} email ngẫu nhiên...")
    print(f"⏱️  Delay giữa các email: {delay} giây\n")
    
    success_count = 0
    fail_count = 0
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            print("✅ Đăng nhập SMTP thành công!\n")
            
            for i in range(count):
                # Chọn ngẫu nhiên một template
                template = random.choice(email_templates)
                
                # Tạo message mới cho mỗi email
                message = MIMEMultipart("alternative")
                message["Subject"] = template["subject"]
                message["From"] = sender_email
                message["To"] = receiver_email
                
                # Gắn HTML vào email
                part = MIMEText(template["html"], "html")
                message.attach(part)
                
                try:
                    # Gửi email
                    server.send_message(message)
                    success_count += 1
                    print(f"✅ Email {i+1}/{count} đã gửi thành công!")
                    print(f"   📧 Subject: {template['subject']}")
                    
                    # Delay giữa các email (trừ email cuối cùng)
                    if i < count - 1:
                        print(f"   ⏳ Chờ {delay} giây...\n")
                        time.sleep(delay)
                    else:
                        print()
                        
                except Exception as e:
                    fail_count += 1
                    print(f"❌ Email {i+1}/{count} gửi thất bại!")
                    print(f"   Error: {e}\n")
                    
    except Exception as e:
        print(f"❌ Lỗi kết nối SMTP: {e}")
        return
    
    # Tổng kết
    print("=" * 50)
    print(f"📊 KẾT QUẢ:")
    print(f"   ✅ Thành công: {success_count}/{count}")
    print(f"   ❌ Thất bại: {fail_count}/{count}")
    print("=" * 50)


# --- Chạy chương trình ---
if __name__ == "__main__":
    # Nhập số lượng email muốn gửi
    try:
        num_emails = int(input("Nhập số lượng email muốn gửi (mặc định 1): ") or "1")
        if num_emails < 1:
            print("⚠️  Số lượng phải >= 1. Sử dụng mặc định: 1")
            num_emails = 1
    except ValueError:
        print("⚠️  Giá trị không hợp lệ. Sử dụng mặc định: 1")
        num_emails = 1
    
    # Nhập delay giữa các email
    try:
        delay_seconds = int(input("Nhập thời gian chờ giữa các email (giây, mặc định 2): ") or "2")
        if delay_seconds < 0:
            print("⚠️  Delay phải >= 0. Sử dụng mặc định: 2")
            delay_seconds = 2
    except ValueError:
        print("⚠️  Giá trị không hợp lệ. Sử dụng mặc định: 2")
        delay_seconds = 2
    
    print()
    send_random_emails(count=num_emails, delay=delay_seconds)
    
# python -m app.tests.read_sync_mail.send_mail
