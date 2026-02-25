import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import engine, Base
from routers import transactions

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: создание таблиц
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup если нужен


app = FastAPI(
    title="AI Finance API",
    description="Backend API для Telegram Mini App финансового учёта",
    version="1.0.0",
    lifespan=lifespan
)

# CORS для Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(transactions.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "AI Finance backend is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
