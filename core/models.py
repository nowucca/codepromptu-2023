from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class Variable(BaseModel):
    name: str
    description: str
    type: str
    expected_format: str = 'text/plain'


class PromptCreate(BaseModel):
    content: str
    input_variables: Optional[List[Variable]] = None
    output_variables: Optional[List[Variable]] = None
    tags: Optional[List[str]] = None
    classification: Optional[str] =None

class Prompt(PromptCreate):
    id: int
    guid: str
    content: str
    author: Optional[int]  # Could be a public prompt, no author
    created_at: datetime
    updated_at: Optional[datetime]  # It's optional since it'll be updated by the service


class User(BaseModel):
    id: int
    guid: str
    username: str
    password: str
