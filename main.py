from fastapi import FastAPI
from fastapi import FastAPI
from web.public_router import public_router
from web.private_router import private_router
from web.dependencies import setup_logging, log_request
from web.middleware import LoggingMiddleware

app = FastAPI()


app.middleware("http")(LoggingMiddleware)

app.add_event_handler("startup", setup_logging)

# Register routers
app.include_router(public_router, prefix="/public", tags=["public"], dependencies=[log_request])
app.include_router(private_router, prefix="/private", tags=["private"], dependencies=[log_request])
