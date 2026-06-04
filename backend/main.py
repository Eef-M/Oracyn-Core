from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import get_settings
from backend.database import create_tables
from backend.api.routes import router as api_router
from backend.api.websocket import router as ws_router
from backend.services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
  """Setup saat startup, cleanup saat shutdown."""
  print(f"🚀 {settings.APP_NAME} starting...")
  create_tables()
  print("✅ Database tables ready")
  start_scheduler()
  yield
  stop_scheduler()
  print("🛑 Server shutdown")

app = FastAPI(
  title=settings.APP_NAME,
  version="1.0.0",
  docs_url="/docs",
  redoc_url="/redoc",
  lifespan=lifespan,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "http://localhost:5173",
    "http://localhost:3000",
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

@app.get("/")
def root():
  return {
    "app":    settings.APP_NAME,
    "docs":   "/docs",
    "status": "running",
  }