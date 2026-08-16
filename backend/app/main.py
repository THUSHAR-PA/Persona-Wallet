from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.routers.accounts import router as accounts_router
from app.routers.transactions import router as transactions_router


app = FastAPI(
    title="Persona Wallet",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts_router)
app.include_router(transactions_router)

@app.get("/")
def home():
    return {
        "message": "Persona Wallet API Running 🚀"
    }


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT version();")
        )

        version = result.scalar()

    return {
        "status": "Connected",
        "database": version
    }