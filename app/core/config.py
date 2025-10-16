"""
Settings management (.env)
Tên trong .env phải giống tên trong class Settings vì nó sẽ tự mapping, 
giá trị đang khởi tạo chỉ là giá trị mặc định tránh lỗi
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # DATABASE SETTINGS
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "arealty_crawler"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # Scheduler settings
    SCHEDULER_TIMEZONE: str = "UTC"
    
    # MAIL
    HOST_IMAP_1: str = 'imap.server'
    EMAIL_ADDRESS_1: str = 'abc@gmail.com'
    EMAIL_PASSWORD_APP_1: str = 'abc'
    
    HOST_IMAP_2: str = 'imap.server'
    EMAIL_ADDRESS_2: str = 'abc@gmail.com'
    EMAIL_PASSWORD_APP_2: str = 'abc'
    
    EMAIL_TIME_RANGE_MINUTES: int = 5  # Lấy email trong N phút gần nhất
    EMAIL_TIME_SEND: int = 1 # Thời gian gửi mail mỗi job
    # Danh sách email được phép, cách nhau bởi dấu phẩy (để trống = cho phép tất cả)
    ALLOWED_SENDERS: str = 'khainam23@gmail.com'  
    # ALLOWED_SENDERS: str = 'noreply@realestate.co.jp' 
    NAME_COLLECTION_MODEL_SEND_MAIL: str = 'model_mail'
    
    # CRM
    URL_CALL_CRM_BMATE: str = "url get"
    KEY_CALL_CRM_BMATE: str = "key"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()