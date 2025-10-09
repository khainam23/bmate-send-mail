"""
FastAPI entrypoint
"""
from fastapi import FastAPI
from app.routes.health import router as health_router
from app.core.scheduler import start_scheduler

app = FastAPI(
    title="Arealty Crawler API",
    description="Real estate data crawler with scheduled jobs",
    version="1.0.0"
)

# Include routers
app.include_router(health_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Start scheduler on application startup"""
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    from app.core.scheduler import stop_scheduler
    stop_scheduler()
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)