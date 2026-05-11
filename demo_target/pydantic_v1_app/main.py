"""FastAPI application entry point for the Pydantic v1 demo target."""

from fastapi import FastAPI

from .routes import router

app = FastAPI(
    title="Bob's Twin Demo Target",
    description="Pydantic v1 app with 4 trap patterns for migration demo",
    version="1.0.0",
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demo_target.pydantic_v1_app.main:app", host="0.0.0.0", port=8001, reload=False)
