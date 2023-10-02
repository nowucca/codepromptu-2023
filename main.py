from fastapi import FastAPI
from web.routers import public_prompts, private_prompts

from web.middleware import LoggingMiddleware

app = FastAPI()

# Register routers

# Include the router with a prefix
app.include_router(public_prompts.router, prefix="/public/prompt", tags=["Public Prompts"])
app.include_router(private_prompts.router, prefix="/private/prompt", tags=["Private Per-user Prompts"])

app.middleware("http")(LoggingMiddleware)
