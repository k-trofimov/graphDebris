import sys

print(sys.path)
import debris
import uvicorn
from fastapi import FastAPI

app = FastAPI()
app.include_router(debris.router, tags=["Debris"], prefix="/api/debris")
origins = [
    "http://localhost:3000",
]


@app.get("/api/healthchecker")
def root():
    return {"message": "Welcome to GraphDebris API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
