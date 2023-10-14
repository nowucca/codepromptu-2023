import traceback

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core.exceptions import PromptException, EXCEPTION_STATUS_CODES
from web.middleware import LoggingMiddleware, RequestIdMiddleware
from web.routers import public_prompts, private_prompts

app = FastAPI()

# Register routers

# Include the router with a prefix
app.include_router(public_prompts.router, prefix="/public", tags=["Public Endpoints"])
app.include_router(private_prompts.router, prefix="/private", tags=["Private Per-user Endpoints"])

# Innermost first
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIdMiddleware)


@app.exception_handler(PromptException)
async def handle_prompt_exception(request, exc: PromptException):
    # Get the status code from our mapping or default to 500 if not found
    status_code = EXCEPTION_STATUS_CODES.get(type(exc), 500)
    traceback_string = traceback.format_exc()
    return JSONResponse(status_code=status_code, content={"detail": str(exc), "traceback": traceback_string})


@app.exception_handler(Exception)
async def handle_generic_exception(request, exc: Exception):
    # Log the exception for debugging (optional)
    print(exc)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})
