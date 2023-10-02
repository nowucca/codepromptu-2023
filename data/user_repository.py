import traceback
from typing import Optional

from data import get_current_db_context


class UserRepositoryInterface:
    def get_user_by_username(self, username: str) -> Optional[dict]:
        pass


class MySQLUserRepository(UserRepositoryInterface):
    def get_user_by_username(self, username: str) -> Optional[dict]:
        db = get_current_db_context()

        try:
            db.cursor.execute("SELECT username, password FROM users WHERE username = %s", (f"{username}",))
            user_rows = [row for row in db.cursor.fetchall()]
            if len(user_rows) == 0:
                return None

            return {"username": user_rows[0]['username'],
                    "password": user_rows[0]['password']}
        except Exception as e:
            traceback.print_exc()
            return None
