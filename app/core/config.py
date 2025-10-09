"""
Settings management (.env)
Tên trong .env phải giống tên trong class Settings vì nó sẽ tự mapping, 
giá trị đang khởi tạo chỉ là giá trị mặc định tránh lỗi
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Scheduler settings
    SCHEDULER_TIMEZONE: str = "UTC"
    
    # MAIL
    HOST_IMAP: str = 'imap.server'
    EMAIL_ADDRESS: str = 'abc@gmail.com'
    EMAIL_PASSWORD_APP: str = 'abc'
    EMAIL_TIME_RANGE_MINUTES: int = 30  # Lấy email trong N phút gần nhất
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()