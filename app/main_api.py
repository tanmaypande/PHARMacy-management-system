from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import check_database_health
from app.api.routes.categories import router as categories_router
from app.api.routes.medicines import router as medicines_router
from app.api.routes.batches import router as batches_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.sales import router as sales_router
from app.api.routes.auth import router as auth_router
from app.api.routes.suppliers import router as suppliers_router
from app.api.routes.customers import router as customers_router
from app.api.routes.purchases import router as purchases_router
from app.api.routes.prescriptions import router as prescriptions_router
from app.api.routes.reports import router as reports_router
from app.api.routes.tqm import router as tqm_router
from app.api.routes.policies import router as policies_router
from app.api.routes.super_admin import router as super_admin_router
from app.api.routes.owner import router as owner_router
from app.api.routes.pharmacist import router as pharmacist_router
from app.api.routes.purchase_orders import router as purchase_orders_router
from app.api.routes.supplier_portal import router as supplier_portal_router
from app.api.routes.customer_portal import router as customer_portal_router
from app.core.db_migration import init_db_and_seed
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables and seed data exist
    init_db_and_seed()
    yield


app = FastAPI(
    title="Pharmacy Management System API",
    description="Multi-Stakeholder Pharmacy SaaS API with TQM Error Prevention and Q12 Accessibility Standards",
    version="2.0.0",
    lifespan=lifespan
)

# Register Domain Routers
app.include_router(dashboard_router)
app.include_router(categories_router)
app.include_router(medicines_router)
app.include_router(batches_router)
app.include_router(sales_router)
app.include_router(auth_router)
app.include_router(suppliers_router)
app.include_router(customers_router)
app.include_router(purchases_router)
app.include_router(prescriptions_router)
app.include_router(reports_router)
app.include_router(tqm_router)
app.include_router(policies_router)
app.include_router(super_admin_router)
app.include_router(owner_router)
app.include_router(pharmacist_router)
app.include_router(purchase_orders_router)
app.include_router(supplier_portal_router)
app.include_router(customer_portal_router)


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
