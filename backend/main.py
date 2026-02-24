from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

from .database import create_db_and_tables
from .routers import auth, watchlists, public, trading, users

app = FastAPI(title="AI-Native Trading Dashboard")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Register Routers
app.include_router(auth.router)
app.include_router(watchlists.router)
app.include_router(public.router)
app.include_router(trading.router)
app.include_router(users.router)

# Static Files & Frontend Orchestration
# Serve frontend assets from /static
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

# Fallback to serve other frontend files directly (app.js, style.css)
@app.get("/{file_name}")
async def serve_frontend_file(file_name: str):
    file_path = os.path.join("frontend", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
