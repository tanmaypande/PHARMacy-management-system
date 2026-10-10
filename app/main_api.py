from fastapi import FastAPI

app = FastAPI(
    title="Pharmacy Management System API",
    description="Backend API for the TQM-focused Pharmacy System",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    """Basic health check endpoint to verify the API is running."""
    return {"status": "ok", "message": "Pharmacy API is running"}

if __name__ == "__main__":
    import uvicorn
    # Run the server locally on port 8000
    uvicorn.run("app.main_api:app", host="127.0.0.1", port=8000, reload=True)
