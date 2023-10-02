from fastapi import FastAPI, HTTPException

from core.exceptions import PromptException, EXCEPTION_STATUS_CODES
from web.routers import public_prompts, private_prompts

from web.middleware import LoggingMiddleware

app = FastAPI()

# Register routers

# Include the router with a prefix
app.include_router(public_prompts.router, prefix="/public/prompt", tags=["Public Prompts"])
app.include_router(private_prompts.router, prefix="/private/prompt", tags=["Private Per-user Prompts"])

app.middleware("http")(LoggingMiddleware)


@app.exception_handler(PromptException)
async def handle_prompt_exception(request, exc: PromptException):
    # Get the status code from our mapping or default to 500 if not found
    status_code = EXCEPTION_STATUS_CODES.get(type(exc), 500)
    return HTTPException(status_code=status_code, detail=str(exc))


@app.exception_handler(Exception)
async def handle_generic_exception(request, exc: Exception):
    # Log the exception for debugging (optional)
    print(exc)
    return HTTPException(status_code=500, detail="An unexpected error occurred.")
