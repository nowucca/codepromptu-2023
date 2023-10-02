import hashlib
import logging
import socket
import threading
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from service import set_request_id, get_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

    async def dispatch(self, request: Request, call_next):
        request_id = self._generate_request_id()
        set_request_id(request_id)
        response: Response = await call_next(request)
        set_request_id("")
        return response

    @staticmethod
    def _generate_request_id():
        current_time = datetime.now().strftime('%Y%m%d%H%M%S%f')
        thread_id = threading.current_thread().ident
        hostname = socket.gethostname()
        request_id = f"{current_time}-{thread_id}-{hostname}"

        return _hashify(request_id)


def _hashify(request_id):
    # Compute sha256 hash and get the first 6 hex digits
    hash_value = hashlib.sha256(request_id.encode()).hexdigest()[:6]
    return hash_value


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        self.log_start(request)
        current_time = datetime.now()
        response: Response = await call_next(request)
        duration = datetime.now() - current_time
        self.log_end(duration, request, response)
        return response

    @staticmethod
    def log_start(request: Request):
        request_id = get_request_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        thread_id = _hashify(str(threading.current_thread().ident))
        request_method = request.method
        request_uri = request.url
        log_string = (f"{current_time} INFO tc=\"{request_id}\" " +
                      f"[{thread_id}] REQUEST START: {request_method} {request_uri}")
        print(log_string)

    @staticmethod
    def log_end(duration, request: Request, response: Response):
        request_id = get_request_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        thread_id = _hashify(str(threading.current_thread().ident))
        request_method = request.method
        request_uri = request.url
        status_code = response.status_code
        log_string = (f"{current_time} INFO tc=\"{request_id}\" "
                      + f"[{thread_id}] REQUEST END: {request_method} {request_uri} "
                      + f"response=\"{status_code}\" duration=\"{duration}ms\"")
        print(log_string)
