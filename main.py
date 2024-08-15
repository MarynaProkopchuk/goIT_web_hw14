import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from src.database.db import get_db
from src.routes import contacts, auth, users
from src.conf.config import config
from ipaddress import ip_address
from typing import Callable
from fastapi.responses import JSONResponse

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
banned_ips = [
    ip_address("192.168.1.1"),
    ip_address("192.168.1.2"),
]

app.include_router(auth.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.middleware("http")
async def ban_ips(request: Request, call_next: Callable):
    try:
        ip = ip_address(request.client.host)
        if ip in banned_ips:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "You are banned"},
            )
    except ValueError:
        pass
    response = await call_next(request)
    return response


redis_client = None


@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = redis.Redis(
        host=config.REDIS_DOMAIN,
        port=config.REDIS_PORT,
        db=0,
        password=config.REDIS_PASSWORD,
    )
    await FastAPILimiter.init(redis_client)


@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()


@app.get("/")
def index():
    return {"message": "Contacts"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
