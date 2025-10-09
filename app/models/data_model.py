"""
Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class JobLog(BaseModel):
    """Job execution log model"""
    id: Optional[str] = Field(None, alias="_id")
    job_name: str = Field(..., description="J`ob name")
    executed_at: datetime = Field(default_factory=datetime.now, description="Execution timestamp")
    status: str = Field(..., description="Job status")
    message: Optional[str] = Field(None, description="Job message")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration: Optional[float] = Field(None, description="Execution duration in seconds")
    records_processed: Optional[int] = Field(None, description="Number of records processed")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: str = Field(default="1.0.0", description="API version")
    database_status: str = Field(..., description="Database connection status")
    scheduler_status: str = Field(..., description="Scheduler status")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }