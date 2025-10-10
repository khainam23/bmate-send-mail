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
    HOST_IMAP: str = 'imap.server'
    EMAIL_ADDRESS: str = 'abc@gmail.com'
    EMAIL_PASSWORD_APP: str = 'abc'
    EMAIL_TIME_RANGE_MINUTES: int = 30  # Lấy email trong N phút gần nhất
    ALLOWED_SENDERS: str = 'abc@gmail.com'  # Danh sách email được phép, cách nhau bởi dấu phẩy (để trống = cho phép tất cả)
    
    # CRM
    URL_CALL_CRM_BMATE: str = "url get"
    KEY_CALL_CRM_BMATE: str = "key"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()