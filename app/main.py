from fastapi import FastAPI
from app.api.routes.users import router as users_router
from app.api.routes.transactions import router as transactions_router

app = FastAPI()

app.include_router(users_router, prefix="/v1", tags=["users"])

app.include_router(transactions_router, prefix="/v1", tags=["transactions"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Balance Service API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)
