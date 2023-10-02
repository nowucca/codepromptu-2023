import logging
from fastapi import Request, Response
from datetime import datetime
import threading

# Import the logging config to ensure it's set up
import logging_config

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)

    async def __call__(self, request: Request, call_next):
        request_id = self._generate_request_id()
        self.log_start(request_id)

        response: Response = await call_next(request)

        self.log_end(request_id, response.status_code)
        return response

    def _generate_request_id(self):
        current_time = datetime.now().strftime('%Y%m%d%H%M%S%f')
        thread_id = threading.current_thread().ident
        request_id = f"{current_time}-{thread_id}"
        return request_id

    def log_start(self, request_id):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        thread_id = threading.current_thread().ident
        log_string = f"{current_time} INFO {request_id} [{thread_id}] REQUEST START"
        self.logger.info(log_string)

    def log_end(self, request_id, status_code):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        thread_id = threading.current_thread().ident
        log_string = f"{current_time} INFO {request_id} [{thread_id}] REQUEST END {status_code}"
        self.logger.info(log_string)
