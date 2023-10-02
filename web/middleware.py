import hashlib
import logging
import socket
import threading
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from service import set_request_id


# Import the logging config to ensure it's set up

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        request_id = self._generate_request_id()
        set_request_id(request_id)
        self.log_start(request_id)

        response: Response = await call_next(request)

        self.log_end(request_id, response.status_code)
        return response

    @staticmethod
    def _generate_request_id():
        current_time = datetime.now().strftime('%Y%m%d%H%M%S%f')
        thread_id = threading.current_thread().ident
        hostname = socket.gethostname()
        request_id = f"{current_time}-{thread_id}-{hostname}"

        # Compute sha256 hash and get the first 6 hex digits
        hash_value = hashlib.sha256(request_id.encode()).hexdigest()[:6]

        return hash_value

    def log_start(self, request_id):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')
        thread_id = threading.current_thread().ident
        log_string = f"{current_time} INFO {request_id} [{thread_id}] REQUEST START"
        self.logger.info(log_string)

    def log_end(self, request_id, status_code):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')
        thread_id = threading.current_thread().ident
        log_string = f"{current_time} INFO {request_id} [{thread_id}] REQUEST END {status_code}"
        self.logger.info(log_string)
