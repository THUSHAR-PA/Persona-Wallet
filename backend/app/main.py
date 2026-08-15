from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.routers.accounts import router as accounts_router


app = FastAPI(
    title="Persona Wallet",
    version="1.0.0"
)


app.include_router(accounts_router)


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