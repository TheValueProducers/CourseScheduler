from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.rank_routes import router as rank_router
from api.review_routes import router as review_router
from api.schedule_routes import router as schedule_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Course Scheduler Backend",
        version="1.0.0",
        description="CP-SAT based course scheduler using Rice catalog data.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "https://course-scheduler-7efc.vercel.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(schedule_router)
    app.include_router(review_router)
    app.include_router(rank_router)
    return app


app = create_app()
