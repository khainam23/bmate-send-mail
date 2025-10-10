import requests
import uuid
import random
import json
from datetime import datetime
from app.core.config import settings


def generate_random_phone():
    """Tạo số điện thoại ngẫu nhiên theo format 8180XXXXXXXX"""
    return f"8180{random.randint(1000, 9999)}{random.randint(1000, 9999)}"


def call_api(extracted_data):
    """
    Gọi API để tạo opportunity trong CRM
    
    Args:
        extracted_data (dict): Dữ liệu đã extract từ email
        
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
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
        
        print(f"🚀 Đang gửi API với dữ liệu: {json.dumps(json_data)}")
        
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


def generate_test_data():
    """Tạo dữ liệu test với UUID và số điện thoại ngẫu nhiên"""
    unique_id = str(uuid.uuid4())[:8]
    
    return {
        'name': f'Dev Test - {unique_id}',
        'email': 'dev.test@bmate.com',
        'phone': generate_random_phone(),
        'content': 'This is a test inquiry from automated testing',
        'contact_date': datetime.now().strftime("%d-%m-%Y"),
    }


def test_single_api_call():
    """Test gọi API một lần với dữ liệu ngẫu nhiên"""
    print("=" * 60)
    print("🧪 TEST: Gọi API một lần")
    print("=" * 60)
    
    test_data = generate_test_data()
    
    result = call_api(test_data)
    
    print("\n" + "=" * 60)
    print(f"📊 KẾT QUẢ: {'✅ THÀNH CÔNG' if result else '❌ THẤT BẠI'}")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
   test_single_api_call()

# Chạy: python -m app.tests.read_sync_mail.test_call_api