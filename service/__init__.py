import logging
import threading
from datetime import datetime

import contextvars

# request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="UNKNOWN")


logging_format = ("%(asctime)s,%(msecs)d %(levelname)s tc=\"%(request_id)s\" [%(thread)d] [%(filename)s:%(lineno)d] %("
                  "message)s")

logging.basicConfig(level=logging.DEBUG, format=logging_format)

logger = logging.getLogger(__name__)


def set_request_id(request_id: str):
    """Set a unique request id for logging."""
    threading.current_thread().request_id = request_id


def get_request_id():
    """Get the unique request id for logging."""
    return getattr(threading.current_thread(), "request_id", "UNKNOWN")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True


logger.addFilter(RequestIdFilter())
