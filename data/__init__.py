# data/init.py

from mysql.connector import pooling
from dotenv import load_dotenv
import os
import threading

load_dotenv()

# Database Configuration
config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'database': os.getenv('DB_NAME'),
    'raise_on_warnings': True
}


# Create a thread-local storage
local_storage = threading.local()

# Create a connection pool
db_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=10, **config)


class DatabaseContext:
    def __enter__(self):
        self.conn = db_pool.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)
        # Store the context in thread-local storage
        local_storage.db_context = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.conn.rollback()  # Rollback transaction if an exception was raised
            self.cursor.close()
            self.conn.close()  # Close the connection regardless of exception status
        finally:
            # Remove context from local storage
            del local_storage.db_context

    @property
    def cursor(self):
        return self._cursor

    # Exposing transactional methods for use in service layer
    def begin_transaction(self):
        self.conn.start_transaction()

    def commit_transaction(self):
        self.conn.commit()

    def rollback_transaction(self):
        self.conn.rollback()

    @cursor.setter
    def cursor(self, value):
        self._cursor = value


# Provide a global function to fetch the current context
def get_current_db_context():
    return getattr(local_storage, "db_context", None)
