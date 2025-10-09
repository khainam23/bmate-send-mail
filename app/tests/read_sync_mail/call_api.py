import requests

url = "https://bmate.getflycrm.com/api/forms/viewform?key=QQtBtzyGuvbDiFLE0Z1w4IO8cCkc1c0V5XWyn8iNh7YeUk8HO6"

payload = {
    "user_id": 0,
    "recipient": None,
    "token_api": "",
    "opportunity_status": None,
    "opp_type_source": "https://bmate.getflycrm.com",
    "op_source_content": "https://bmate.getflycrm.com",
    "account_type": [],
    "account_name": "Test",
    "account_description": "Test",
    "account_email": "1111111@gmail.com",
    "account_phone": "09053731350",
    "custom_fields": {
        "ngay_khach_contact": "02/10/2025",
        "visa": "11",
        "ngay_du_kien_vao_nha": "09/10/2025",
        "ngan_sach_tien_thue": "150000",
        "overseas_dang_o_nhat": "8",
        "nuoi_pet": "",
        "nen_tang_lien_he": "1"
    },
    "utm_params": {
        "utm_source": "",
        "utm_campaign": "",
        "utm_medium": "",
        "utm_content": "",
        "utm_term": "",
        "utm_user": "",
        "utm_account": ""
    }
}

headers = {"Content-Type": "application/json"}
response = requests.get(url, json=payload, headers=headers)
print(response.status_code, response.text)