
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings

# --- Cấu hình người gửi và người nhận ---
sender_email = settings.EMAIL_ADDRESS
receiver_email = settings.EMAIL_ADDRESS
password = settings.EMAIL_PASSWORD_APP  # dùng App Password nếu là Gmail

# --- Tạo nội dung email ---
message = MIMEMultipart("alternative")
message["Subject"] = "New Inquiry Lead from Real Estate Japan"
message["From"] = sender_email
message["To"] = receiver_email

# --- HTML Template ---
html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { background-color: #1e1e1e; color: #ddd; font-family: Arial, sans-serif; padding: 20px; }
    .container { background-color: #2c2c2c; padding: 20px; border-radius: 8px; width: 600px; margin: auto; }
    h2 { color: #9bcb48; }
    * {color: white;}
    a { color: #52a8ff; text-decoration: none; }
    .section { margin-bottom: 20px; }
    .label { font-weight: bold; color: #fff; }
  </style>
</head>
<body>
  <div class="container">
    <h2><img src="https://realestate.co.jp/favicon.ico" alt="logo" style="vertical-align:middle;margin-right:10px;">realestatejapan</h2>
    <p>The following is an inquiry lead from Real Estate Japan. Please respond to the client as soon as possible.</p>
    
    <div class="section">
      <p class="label">Property details:</p>
      <p>Property link: <a href="https://realestate.co.jp/en/rent/view/1280512">https://realestate.co.jp/en/rent/view/1280512</a><br>
         Property ID: 1280512<br>
         Property Type: For Rent<br>
         Building name: Ka F+style Hagoromo Building No. 5<br>
         Unit number: 202
      </p>
    </div>

    <div class="section">
      <p class="label">Customer details:</p>
      <p>Name: Kyle Chew<br>
         Email: <a href="mailto:khye.chew@gmail.com">khye.chew@gmail.com</a><br>
         Approximate Move-In Date: 10/23/2025<br>
         Inquiry: Hello, I'm wondering if this still available
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

# --- Gắn HTML vào email ---
part = MIMEText(html, "html")
message.attach(part)

# --- Gửi mail ---
try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.send_message(message)
        print("✅ Email sent successfully!")
except Exception as e:
    print("❌ Error:", e)
