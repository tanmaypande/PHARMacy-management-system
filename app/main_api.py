from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import check_database_health

app = FastAPI(
    title="Pharmacy Management System API",
    description="Backend API with TQM Error Prevention and Q12 Accessibility Standards",
    version="1.0.0"
)

@app.get("/health", tags=["Health & Monitoring"])
def health_check():
    """
    Comprehensive system health check.
    Verifies that the API service is responsive and tests the live connection to PostgreSQL.
    """
    db_status = check_database_health()
    is_healthy = db_status.get("database_connected", False)
    
    response_payload = {
        "status": "healthy" if is_healthy else "degraded",
        "api_service": "running",
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }
    
    # Return 200 OK if healthy, 503 Service Unavailable if database is unreachable
    http_status = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=http_status, content=response_payload)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
