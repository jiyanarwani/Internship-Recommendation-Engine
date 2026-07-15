import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import Config
from database import engine
from sqlmodel import SQLModel

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("app")

# Import routers
from routes.auth_routes import auth_router
from routes.candidate_routes import candidate_router
from routes.admin_routes import admin_router
from routes.main_routes import main_router

# Let's import models so that metadata has them registered
import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables initialized.")
    yield
    logger.info("Shutting down application...")

app = FastAPI(lifespan=lifespan, title="Internship Recommendation Engine API")

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Session Middleware
app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Routers


app.include_router(auth_router, prefix="/api/auth")
app.include_router(candidate_router, prefix="/api/candidate")
app.include_router(admin_router, prefix="/api/admin")
app.include_router(main_router)  # Root path operations

if __name__ == '__main__':
    import uvicorn
    # Runs uvicorn on port 5000
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
