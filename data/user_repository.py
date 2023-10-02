import traceback
from typing import Optional

from core.models import User
from data import get_current_db_context


class UserRepositoryInterface:
    def get_user_by_username(self, username: str) -> Optional[User]:
        pass


class MySQLUserRepository(UserRepositoryInterface):
    def get_user_by_username(self, username: str) -> Optional[User]:
        db = get_current_db_context()

        try:
            db.cursor.execute("SELECT id, guid, username, password FROM users WHERE username = %s", (f"{username}",))
            user_rows = [row for row in db.cursor.fetchall()]
            if len(user_rows) == 0:
                return None
            else:
                row = user_rows[0]
                return User(id=row['id'], guid=row['guid'], username=row['username'], password=row['password'])
        except Exception as e:
            traceback.print_exc()
            return None
