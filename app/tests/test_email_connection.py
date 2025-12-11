"""
Test file để kiểm tra kết nối email (SMTP và IMAP)
Chạy: python -m app.tests.read_sync_mail.test_email_connection
"""

import smtplib
import imaplib
from app.core.config import settings


def test_smtp_connection():
    """Kiểm tra kết nối SMTP (gửi email)"""
    print("=" * 60)
    print("🔍 KIỂM TRA KẾT NỐI SMTP")
    print("=" * 60)
    
    try:
        print(f"📧 Email: {settings.EMAIL_ADDRESS_3}")
        print(f"🔐 Đang kết nối đến smtp.gmail.com:465...")
        
        # Kết nối SMTP SSL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            print("✅ Kết nối SMTP thành công!")
            
            # Đăng nhập
            print(f"🔑 Đang đăng nhập...")
            server.login(settings.EMAIL_ADDRESS_3, settings.EMAIL_PASSWORD_APP_3)
            print("✅ Đăng nhập SMTP thành công!")
            
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Lỗi xác thực SMTP: {e}")
        print("💡 Kiểm tra lại email và App Password")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ Lỗi SMTP: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        return False


def test_imap_connection():
    """Kiểm tra kết nối IMAP (đọc email)"""
    print("\n" + "=" * 60)
    print("🔍 KIỂM TRA KẾT NỐI IMAP")
    print("=" * 60)
    
    try:
        print(f"📧 Email: {settings.EMAIL_ADDRESS_3}")
        print(f"🔐 Đang kết nối đến imap.gmail.com:993...")
        
        # Kết nối IMAP SSL
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=10)
        print("✅ Kết nối IMAP thành công!")
        
        # Đăng nhập
        print(f"🔑 Đang đăng nhập...")
        mail.login(settings.EMAIL_ADDRESS_3, settings.EMAIL_PASSWORD_APP_2)
        print("✅ Đăng nhập IMAP thành công!")
        
        # Liệt kê các mailbox
        print(f"📂 Đang kiểm tra mailbox...")
        status, mailboxes = mail.list()
        if status == 'OK':
            print(f"✅ Tìm thấy {len(mailboxes)} mailbox")
            
        # Chọn INBOX
        status, messages = mail.select('INBOX')
        if status == 'OK':
            message_count = int(messages[0])
            print(f"✅ INBOX có {message_count} email")
        
        # Đóng kết nối
        mail.close()
        mail.logout()
        print("✅ Đóng kết nối IMAP thành công!")
        
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"❌ Lỗi IMAP: {e}")
        print("💡 Kiểm tra lại email và App Password")
        return False
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        return False


def main():
    """Chạy tất cả các test"""
    print("\n" + "🚀 " * 20)
    print("BẮT ĐẦU KIỂM TRA KẾT NỐI EMAIL")
    print("🚀 " * 20 + "\n")
    
    smtp_ok = test_smtp_connection()
    imap_ok = test_imap_connection()
    
    # Tổng kết
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TỔNG HỢP")
    print("=" * 60)
    print(f"SMTP (Gửi email): {'✅ OK' if smtp_ok else '❌ FAILED'}")
    print(f"IMAP (Đọc email): {'✅ OK' if imap_ok else '❌ FAILED'}")
    print("=" * 60)
    
    if smtp_ok and imap_ok:
        print("\n🎉 TẤT CẢ KẾT NỐI HOẠT ĐỘNG BÌNH THƯỜNG!")
        return True
    else:
        print("\n⚠️  MỘT HOẶC NHIỀU KẾT NỐI BỊ LỖI!")
        print("\n💡 Hướng dẫn khắc phục:")
        print("1. Kiểm tra EMAIL_ADDRESS_2 và EMAIL_PASSWORD_APP_2 trong file .env")
        print("2. Đảm bảo đã bật 2-Step Verification cho Gmail")
        print("3. Tạo App Password tại: https://myaccount.google.com/apppasswords")
        print("4. Đảm bảo IMAP đã được bật trong Gmail Settings")
        return False


if __name__ == "__main__":
    main()
