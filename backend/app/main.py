from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine

app = FastAPI(
    title="Persona Wallet",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Persona Wallet API Running 🚀"
    }


@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.scalar()

    return {
        "status": "Connected",
        "database": version
    }