import traceback
from typing import List, Optional

from core import make_guid
from core.exceptions import ConstraintViolationError, DataValidationError, UnauthorizedError
from core.models import Prompt, Variable, User, PromptCreate
from data import get_current_db_context


class PromptRepositoryInterface:
    def create_prompt(self, prompt: PromptCreate, author: Optional[User] = None) -> str:
        raise NotImplementedError

    def update_prompt(self, prompt: Prompt, user: Optional[User] = None) -> None:
        raise NotImplementedError

    def delete_prompt(self, guid: str, user: Optional[User] = None) -> None:
        raise NotImplementedError

    def get_prompt(self, guid: str, user: Optional[User] = None) -> Prompt:
        raise NotImplementedError

    def list_prompts(self, user: Optional[User] = None) -> List[Prompt]:
        raise NotImplementedError

    def add_remove_tags_for_prompt(self, guid: str, tags: List[str], user: Optional[User] = None) -> None:
        raise NotImplementedError

    def add_remove_classification_for_prompt(self, guid: str, classification: str, user: Optional[User] = None) -> None:
        raise NotImplementedError

    def search_prompts(self, query: str, user: Optional[User] = None) -> List[Prompt]:
        raise NotImplementedError

    def get_prompts_by_tag(self, tag: str, user: Optional[User] = None) -> List[Prompt]:
        raise NotImplementedError

    def get_prompts_by_classification(self, classification: str, user: Optional[User] = None) -> List[Prompt]:
        raise NotImplementedError


class MySQLPromptRepository(PromptRepositoryInterface):

    def create_prompt(self, prompt: PromptCreate, author: Optional[User] = None) -> str:
        db = get_current_db_context()
        try:
            prompt_guid = make_guid()
            # Insert main prompt data
            db.cursor.execute("INSERT INTO prompts (guid, content, author_id ) VALUES (%s, %s, %s)",
                              (prompt_guid, prompt.content, author.id if author else None,))
            prompt_id = db.cursor.lastrowid

            # Handle I/O variables
            for var in prompt.input_variables + prompt.output_variables:
                guid = make_guid()
                db.cursor.execute(
                    "INSERT INTO io_variables (guid, name, description, expected_format, type) VALUES (%s, %s, %s, %s, %s)",
                    (
                        guid, var.name, var.description, var.expected_format,
                        'input' if var in prompt.input_variables else 'output'))
                io_variable_id = db.cursor.lastrowid
                db.cursor.execute("INSERT INTO prompt_io_variables (prompt_id, io_variable_id) VALUES (%s, %s)",
                                  (prompt_id, io_variable_id))

            self._store_tags_classification(prompt, prompt_id)

            return prompt_guid
        except Exception as e:
            traceback.print_exc()
            if 'constraint' in str(e).lower():
                raise ConstraintViolationError(message=f"Error occurred while saving the prompt: {e}")
            else:
                raise DataValidationError(message=f"Error occurred while saving the prompt: {e}")

    def _store_tags_classification(self, prompt, prompt_id):
        db = get_current_db_context()
        # Handle tags
        if prompt.tags:
            for tag in prompt.tags:
                db.cursor.execute("INSERT IGNORE INTO tags (tag_name) VALUES (%s)", (tag,))
                db.cursor.execute("SELECT id FROM tags WHERE tag_name = %s", (tag,))
                tag_id = db.cursor.fetchone()['id']
                db.cursor.execute("INSERT INTO prompt_tags (prompt_id, tag_id) VALUES (%s, %s)",
                                  (prompt_id, tag_id))
        # Handle classification
        if prompt.classification:
            db.cursor.execute("INSERT IGNORE INTO classifications (classification_name) VALUES (%s)",
                              (prompt.classification,))
            db.cursor.execute("SELECT id FROM classifications WHERE classification_name = %s", (prompt.classification,))
            classification_id = db.cursor.fetchone()['id']
            db.cursor.execute("UPDATE prompts SET classification_id = %s WHERE id = %s",
                              (classification_id, prompt_id))

    def get_prompt(self, guid: str, user: Optional[User] = None) -> Optional[Prompt]:
        db = get_current_db_context()
        try:
            # Fetch basic prompt data
            if user:
                db.cursor.execute("""
                            SELECT * FROM prompts WHERE guid = %s AND author_id = %s
                        """, (guid, user.id))
            else:
                db.cursor.execute("""
                            SELECT * FROM prompts WHERE guid = %s AND author_id IS NULL
                        """, (guid,))

            prompt_row = db.cursor.fetchone()
            if not prompt_row:
                return None

            # Fetch associated I/O variables
            db.cursor.execute("SELECT * FROM prompt_io_variables WHERE prompt_id = %s", (prompt_row['id'],))
            io_variable_ids = [row['io_variable_id'] for row in db.cursor.fetchall()]
            db.cursor.execute("SELECT * FROM io_variables WHERE id IN (%s)", (",".join(map(str, io_variable_ids)),))

            input_vars = []
            output_vars = []
            for row in db.cursor.fetchall():
                var = Variable(name=row['name'], description=row['description'], expected_format=row['expected_format'])
                # Assuming you have a field to distinguish between input and output variables
                if row['type'] == 'input':
                    input_vars.append(var)
                else:
                    output_vars.append(var)

            # Fetch associated tags
            db.cursor.execute(
                "SELECT tag_name FROM tags WHERE id IN (SELECT tag_id FROM prompt_tags WHERE prompt_id = %s)",
                (prompt_row['id'],))
            tags = [row['tag_name'] for row in db.cursor.fetchall()]

            # Fetch classification
            db.cursor.execute("SELECT classification_name FROM classifications WHERE id = %s",
                              (prompt_row['classification_id'],))
            classification = db.cursor.fetchone()['classification_name']

            # Construct and return the Prompt model
            return Prompt(
                guid=prompt_row['guid'],
                id=prompt_row['id'],
                content=prompt_row['content'],
                input_variables=input_vars,
                output_variables=output_vars,
                tags=tags,
                classification=classification,
                author=prompt_row['author_id'],  # assuming author_id maps to an author name or similar
                readonly=prompt_row['readonly'],
                created_at=prompt_row['created_at'],
                updated_at=prompt_row['updated_at'] if 'updated_at' in prompt_row else None,

            )
        except Exception as e:
            traceback.print_exc()
            if 'constraint' in str(e).lower():
                raise ConstraintViolationError(message=f"Error occurred while reading the prompt: {e}")
            else:
                raise DataValidationError(message=f"Error occurred while reading the prompt: {e}")

    def update_prompt(self, prompt: Prompt, user: Optional[User] = None) -> None:
        db = get_current_db_context()

        self._check_prompt_ownership(prompt.guid, user)

        try:
            # Update main prompt content
            db.cursor.execute("UPDATE prompts SET content = %s, updated_at = CURRENT_TIMESTAMP WHERE guid = %s",
                              (prompt.content, prompt.guid))

            # Update I/O variables. For simplicity, we'll remove all current associations and re-add them
            db.cursor.execute("SELECT id FROM prompts WHERE guid = %s", (prompt.guid,))
            prompt_id = db.cursor.fetchone()['id']
            db.cursor.execute("DELETE FROM prompt_io_variables WHERE prompt_id = %s", (prompt_id,))

            for var in prompt.input_variables + prompt.output_variables:
                variable_guid = make_guid()
                db.cursor.execute("""
                    INSERT INTO io_variables (guid, name, description, expected_format, type) 
                    VALUES (%s, %s, %s, %s, %s) 
                    ON DUPLICATE KEY UPDATE name = %s, description = %s, expected_format = %s
                
                """,
                    (variable_guid, var.name, var.description, var.expected_format,
                     'input' if var in prompt.input_variables else 'output',
                     var.name, var.description, var.expected_format))
                io_variable_id = db.cursor.lastrowid
                db.cursor.execute("INSERT INTO prompt_io_variables (prompt_id, io_variable_id) VALUES (%s, %s)",
                                  (prompt_id, io_variable_id))

            self._store_tags_classification(prompt, prompt_id)

        except Exception as e:
            traceback.print_exc()
            if 'constraint' in str(e).lower():
                raise ConstraintViolationError(message=f"Error occurred while updating the prompt: {e}")
            else:
                raise DataValidationError(message=f"Error occurred while updating the prompt: {e}")

    @staticmethod
    def _check_prompt_ownership(guid, user):
        db = get_current_db_context()
        query = "SELECT author_id FROM prompts WHERE guid = %s"
        params = (guid,)
        db.cursor.execute(query, params)
        author_id = db.cursor.fetchone()['author_id']
        if author_id != (user.id if user else None):
            raise UnauthorizedError(f"Attempting to update a prompt that does not belong to the user or is not NULL.")

    def delete_prompt(self, guid: str, user: Optional[User] = None) -> None:
        db = get_current_db_context()
        self._check_prompt_ownership(guid, user)

        try:
            # Fetch the ID for the given prompt guid
            db.cursor.execute("SELECT id FROM prompts WHERE guid = %s", (guid,))
            prompt_id = db.cursor.fetchone()['id']

            # Remove associations
            db.cursor.execute("DELETE FROM prompt_io_variables WHERE prompt_id = %s", (prompt_id,))
            db.cursor.execute("DELETE FROM prompt_tags WHERE prompt_id = %s", (prompt_id,))
            # Remove the main prompt
            db.cursor.execute("DELETE FROM prompts WHERE id = %s", (prompt_id,))
        except Exception as e:
            traceback.print_exc()
            if 'constraint' in str(e).lower():
                raise ConstraintViolationError(message=f"Error occurred while deleting the prompt: {e}")
            else:
                raise DataValidationError(message=f"Error occurred while deleting the prompt: {e}")

    def list_prompts(self, user: Optional[User] = None) -> List[Prompt]:
        db = get_current_db_context()

        try:
            # Adjust the query based on the presence of the user parameter
            if user:
                db.cursor.execute("""
                            SELECT * FROM prompts WHERE author_id = %s
                        """, (user.id,))
            else:
                db.cursor.execute("""
                            SELECT * FROM prompts WHERE author_id IS NULL
                        """)
            prompt_datas = db.cursor.fetchall()

            prompts = []
            for prompt_data in prompt_datas:
                # For each prompt, fetch the associated I/O variables
                db.cursor.execute("""
                    SELECT io_variables.*
                    FROM io_variables 
                    INNER JOIN prompt_io_variables ON io_variables.id = prompt_io_variables.io_variable_id 
                    WHERE prompt_io_variables.prompt_id = %s
                """, (prompt_data['id'],))
                io_vars = db.cursor.fetchall()
                input_vars = [Variable(**var) for var in io_vars if var['type'] == 'input']
                output_vars = [Variable(**var) for var in io_vars if var['type'] == 'output']

                # Fetch associated tags
                db.cursor.execute("""
                    SELECT tags.tag_name
                    FROM tags
                    INNER JOIN prompt_tags ON tags.id = prompt_tags.tag_id
                    WHERE prompt_tags.prompt_id = %s
                """, (prompt_data['id'],))
                tags = [row['tag_name'] for row in db.cursor.fetchall()]

                # Fetch classification
                db.cursor.execute("SELECT classification_name FROM classifications WHERE id = %s",
                                  (prompt_data['classification_id'],))
                result = db.cursor.fetchone()

                if result is None or result['classification_name'] is None:
                    classification = None
                else:
                    classification = result['classification_name']

                # Construct and append the Prompt object to the list
                prompts.append(Prompt(guid=prompt_data['guid'],
                                      id=prompt_data['id'],
                                      content=prompt_data['content'],
                                      input_variables=input_vars,
                                      output_variables=output_vars,
                                      tags=tags,
                                      classification=classification,
                                      author=prompt_data['author_id'],
                                      created_at=prompt_data['created_at'],
                                      updated_at=prompt_data['updated_at']))

            return prompts
        except Exception as e:
            traceback.print_exc()
            if 'constraint' in str(e).lower():
                raise ConstraintViolationError(message=f"Error occurred while listing the prompts: {e}")
            else:
                raise DataValidationError(message=f"Error occurred while listing the prompts: {e}")

    def add_remove_tags_for_prompt(self, guid: str, tags: List[str], user: Optional[User] = None) -> None:
        db = get_current_db_context()
        self._check_prompt_ownership(guid, user)
        try:
            # Fetch the ID for the given prompt guid
            if user:
                db.cursor.execute("""
                            SELECT id FROM prompts WHERE guid = %s AND author_id = %s
                        """, (guid, user.id,))
            else:
                db.cursor.execute("""
                            SELECT id FROM prompts WHERE guid = %s AND author_id IS NULL
                        """, (guid,))
            prompt_id = db.cursor.fetchone()['id']

            # Get the existing tags for the prompt
            db.cursor.execute("""
                    SELECT tags.tag_name
                    FROM tags
                    INNER JOIN prompt_tags ON tags.id = prompt_tags.tag_id
                    WHERE prompt_tags.prompt_id = %s
                """, (prompt_id,))
            existing_tags = [row['tag_name'] for row in db.cursor.fetchall()]

            # Identify tags to be added and tags to be removed
            tags_to_add = set(tags) - set(existing_tags)
            tags_to_remove = set(existing_tags) - set(tags)

            for tag in tags_to_add:
                # Check if tag exists in the main tags table
                db.cursor.execute("SELECT id FROM tags WHERE tag_name = %s", (tag,))
                tag_id = db.cursor.fetchone()
                if not tag_id:
                    tag_guid = make_guid()
                    db.cursor.execute("INSERT INTO tags(guid, tag_name) VALUES (%s, %s)", (tag_guid, tag,))
                    tag_id = db.cursor.fetchone()['id']

                # Add the tag association to the prompt
                db.cursor.execute("INSERT INTO prompt_tags(prompt_id, tag_id) VALUES (%s, %s)", (prompt_id, tag_id))

            for tag in tags_to_remove:
                db.cursor.execute("""
                        DELETE FROM prompt_tags 
                        WHERE prompt_id = %s AND tag_id = (SELECT id FROM tags WHERE tag_name = %s)
                    """, (prompt_id, tag))
        except Exception as e:
            traceback.print_exc()
            if 'constraint' in str(e).lower():
                raise ConstraintViolationError(message=f"Error occurred while changing tags on the prompts: {e}")
            else:
                raise DataValidationError(message=f"Error occurred while  changing tags on the prompts: {e}")

    def add_remove_classification_for_prompt(self, guid: str, classification: str, user: Optional[User] = None) -> None:
        db = get_current_db_context()
        self._check_prompt_ownership(guid, user)

        try:
            # Check if the classification exists in the classifications table
            db.cursor.execute("SELECT id FROM classifications WHERE classification_name = %s", (classification,))
            classification_id = db.cursor.fetchone()
            if not classification_id:
                classification_guid = make_guid()
                db.cursor.execute("INSERT INTO classifications(guid, classification_name) VALUES (%s,%s)", (classification_guid, classification,))
                classification_id = db.cursor.fetchone()['id']

            # Update the prompt's classification
            db.cursor.execute("UPDATE prompts SET classification_id = %s WHERE guid = %s", (classification_id, guid))
        except Exception as e:
            traceback.print_exc()
            if 'constraint' in str(e).lower():
                raise ConstraintViolationError(
                    message=f"Error occurred while add_remove_classifications_for_prompt: {e}")
            else:
                raise DataValidationError(message=f"Error occurred while add_remove_classifications_for_prompt: {e}")

    def search_prompts(self, query: str, user: Optional[User] = None) -> List[Prompt]:
        db = get_current_db_context()

        # Fetch matching prompt guids based on the query (I assume a simple LIKE clause for now)
        # Adjust the query based on the presence of the user parameter
        if user:
            db.cursor.execute("""
                    SELECT guid FROM prompts 
                    WHERE content LIKE %s AND author_id = %s
                """, (f"%{query}%", user.id))
        else:
            db.cursor.execute("""
                    SELECT guid FROM prompts 
                    WHERE content LIKE %s AND author_id IS NULL
                """, (f"%{query}%",))

        prompt_guids = [row['guid'] for row in db.cursor.fetchall()]

        # Map guids to their full details
        return [self.get_prompt(guid) for guid in prompt_guids]

    def get_prompts_by_tag(self, tag: str, user: Optional[User] = None) -> List[Prompt]:
        db = get_current_db_context()

        # Fetch prompt guids that have the given tag
        # Adjust the query based on the presence of the user parameter
        if user:
            db.cursor.execute("""
                    SELECT prompts.guid FROM prompts 
                    JOIN prompt_tags ON prompts.id = prompt_tags.prompt_id 
                    JOIN tags ON prompt_tags.tag_id = tags.id 
                    WHERE tags.tag_name = %s AND prompts.author_id = %s
                """, (tag, user.id))
        else:
            db.cursor.execute("""
                    SELECT prompts.guid FROM prompts 
                    JOIN prompt_tags ON prompts.id = prompt_tags.prompt_id 
                    JOIN tags ON prompt_tags.tag_id = tags.id 
                    WHERE tags.tag_name = %s AND prompts.author_id IS NULL
                """, (tag,))
        prompt_guids = [row['guid'] for row in db.cursor.fetchall()]

        # Map guids to their full details
        return [self.get_prompt(guid) for guid in prompt_guids]

    def get_prompts_by_classification(self, classification: str, user: Optional[User] = None) -> List[Prompt]:
        db = get_current_db_context()

        # Fetch prompt guids that have the given classification
        # Adjust the query based on the presence of the user parameter
        if user:
            db.cursor.execute("""
                    SELECT prompts.guid FROM prompts 
                    JOIN classifications ON prompts.classification_id = classifications.id 
                    WHERE classifications.classification_name = %s AND prompts.author_id = %s
                """, (classification, user.id))
        else:
            db.cursor.execute("""
                    SELECT prompts.guid FROM prompts 
                    JOIN classifications ON prompts.classification_id = classifications.id 
                    WHERE classifications.classification_name = %s AND prompts.author_id IS NULL
                """, (classification,))
        prompt_guids = [row['guid'] for row in db.cursor.fetchall()]

        # Map guids to their full details
        return [self.get_prompt(guid) for guid in prompt_guids]
