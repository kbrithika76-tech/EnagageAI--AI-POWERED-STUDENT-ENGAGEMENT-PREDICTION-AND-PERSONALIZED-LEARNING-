"""
EngageAI Backend — main.py

FastAPI Application Entry Point.
  - Mounts CORS middleware for frontend communication.
  - Loads ML model & preprocessor via lifespan context manager on startup.
  - Mounts all API routers under /api.
  - Serves static reports and figures if required.
"""

import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from backend.database import Base, engine
from backend.database.seed import seed_database
from backend.services.ml_service import ml_service

from backend.routes.auth import router as auth_router
from backend.routes.students import router as students_router
from backend.routes.content import router as content_router
from backend.routes.quizzes import router as quizzes_router
from backend.routes.activity import router as activity_router
from backend.routes.prediction import router as prediction_router
from backend.routes.explanation import router as explanation_router
from backend.routes.recommendations import router as recommendations_router
from backend.routes.courses import router as courses_router
from backend.routes.teacher import router as teacher_router
from backend.routes.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print("=" * 60)
    print("EngageAI Backend Initializing...")
    print("=" * 60)
    
    # 1. Initialize DB tables & seed initial data
    seed_database()

    # 2. Load ML model and preprocessor singleton
    ml_service.load()

    print("\nEngageAI Backend Server Ready!")
    print("=" * 60)
    yield
    # Shutdown actions
    print("EngageAI Backend Shutting Down...")


app = FastAPI(
    title="EngageAI API",
    description="Backend API for Explainable Student Engagement Prediction Framework",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(quizzes_router, prefix="/api")
app.include_router(activity_router, prefix="/api")
app.include_router(prediction_router, prefix="/api")
app.include_router(explanation_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(teacher_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Serve outputs/figures static directory for XAI plots if needed
figures_dir = os.path.join(PROJECT_ROOT, "outputs", "figures")
if os.path.exists(figures_dir):
    app.mount("/figures", StaticFiles(directory=figures_dir), name="figures")


@app.get("/")
def root():
    return {
        "status": "online",
        "app": "EngageAI Student Engagement Prediction System API",
        "docs": "/docs"
    }
