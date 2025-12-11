import logging
from datetime import datetime
import requests

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

def parse_timestamp_to_date(self, timestamp, date_format='%d-%m-%Y'):
    if not isinstance(timestamp, int):
        return None
    
    try:
        dt = datetime.fromtimestamp(timestamp).astimezone()
        return dt.strftime(date_format)
    except Exception as e:
        logger.warning(f"⚠️ Không thể parse timestamp: {e}")
        return None


def sendKintone(data: dict):
    if data is None:
        logger.info("ℹ️  Không có dữ liệu để gửi API")
        return

    # _id = data.get('_id', None)
    contact_date = parse_timestamp_to_date(data.get("contact_date", None))
    customer_name = data.get("name", None)
    phone = data.get("phone", None)
    # visa = data.get('visa', None)
    overseas = data.get('overseas', None)
    # pet = data.get('pet', None)
    email = data.get("email", None)
    move_in_time = parse_timestamp_to_date(data.get("date", None))
    total_monthly = data.get('budget', 0)
    
    extra_info = data.get('content')

    payload = {
        "app": settings.KINTONE_APP_ID,
        "record": {
            "Lead_date": {"value": contact_date or None},
            "Customer_Name": {"value": customer_name or None},
            "Source": {"value": "Gaijinpot"},
            "Check_box": {"value": ["Email"]},
            "Text_1": {"value": phone or None},
            "Text_0": {"value": email or None},
            "Hearing": {"value": extra_info or None},
            "Date": {"value": move_in_time or None},
            "Source_Type": {"value": None},
            "Drop_down_6": {"value": None},
            "Drop_down_7": {"value": None},
            "Oversea": {"value": "Yes" if overseas else None},
            "Visa": {"value": None},
            "Drop_down_3": {"value": None},
            "Drop_down_0": {"value": "New Leads"},
            "VN_in_charge": {"value": "IT"},
            "Responded": {"value": []},
            "Oversea": {"value": []},
            "Rent_budget": {"value": total_monthly},
        }
    }

    try:
        response = requests.post(
            settings.KINTONE_URL,
            headers={
                'X-Cybozu-API-Token': settings.KINTONE_API,
                'Content-Type': 'application/json'
            },
            json=payload
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"POST failed: {e}", exc_info=True)