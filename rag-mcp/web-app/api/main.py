from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.categories import router as categories_router
from routes.questions import router as questions_router

app = FastAPI(title="FAQ Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories_router)
app.include_router(questions_router)


@app.get("/")
def root():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)