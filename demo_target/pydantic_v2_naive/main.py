"""Naive Pydantic v2 migration app — runs on port 8002."""

from fastapi import FastAPI

from .routes import router

app = FastAPI(
    title="Bob's Twin Demo — Naive v2 Migration",
    description="What bump-pydantic produces WITHOUT fixing the 4 trap patterns",
    version="2.0.0-naive",
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demo_target.pydantic_v2_naive.main:app", host="0.0.0.0", port=8002, reload=False)
