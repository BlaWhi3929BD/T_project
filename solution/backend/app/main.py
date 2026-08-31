from fastapi import FastAPI

app = FastAPI(title="Trades Dashboard API")

@app.get("/")
async def root():
    return {"message": "Trades Dashboard API is running"}
