from fastapi import APIRouter, Depends, HTTPException, Query

from core.exceptions import RecordNotFoundError
from core.models import Prompt, User, PromptCreate, PromptUpdate
from service.prompt_service import PromptServiceInterface
from typing import List

from web.dependencies import get_prompt_service, require_admin_user

router = APIRouter()


@router.post("/prompt/", status_code=201, summary="Add a New Prompt (requires admin user)")
async def add_prompt(prompt: PromptCreate,
                     service: PromptServiceInterface = Depends(get_prompt_service),
                     user: User = Depends(require_admin_user)):
    return service.create_prompt(prompt)

@router.delete("/prompt/{guid}", status_code=204, summary="Delete a Public Prompt by GUID (requires admin user)")
def delete_prompt(guid: str,
                        service: PromptServiceInterface = Depends(get_prompt_service),
                        user: User = Depends(require_admin_user)):
    service.delete_prompt(guid)
    return {}  # Return an empty response for 204 status

@router.put("/prompt/{guid}", status_code=204, summary="Update a Public Prompt by GUID (requires admin user) ")
def update_prompt(guid: str, prompt: PromptCreate, service: PromptServiceInterface = Depends(get_prompt_service),
                        user: User = Depends(require_admin_user)):
    # Fill in the PromptUpdate constructor below with named params
    service.update_prompt(PromptUpdate(content=prompt.content,
                                              input_variables=prompt.input_variables,
                                              output_variables=prompt.output_variables,
                                              tags=prompt.tags,
                                              classification=prompt.classification,
                                              guid=guid))
    return {}  # Return an empty response for 204 status

@router.get("/prompt/{guid}", response_model=Prompt, summary="Retrieve a Public Prompt by GUID")
def get_prompt(guid: str, service: PromptServiceInterface = Depends(get_prompt_service)):
    try:
        return service.get_prompt(guid)
    except RecordNotFoundError:
        raise HTTPException(status_code=404, detail="Prompt not found")


@router.get("/prompt/", response_model=List[Prompt], summary="List all Public Prompts")
def list_prompts(skip: int = 0, limit: int = 10, service: PromptServiceInterface = Depends(get_prompt_service)):
    # Using pagination with skip and limit.
    # You can enhance this further by allowing filters like tags, authors, etc.
    return service.list_prompts()[skip: skip+limit]


@router.get("/prompt/search/", response_model=List[Prompt], summary="Search Public Prompts")
def search_prompts(query: str, service: PromptServiceInterface = Depends(get_prompt_service)):
    # Assuming the service has a method to search prompts. This can be implemented in various ways.
    return service.search_prompts(query)


@router.get("/prompt/tags/",
            response_model=List[Prompt], summary="List Public Prompts by Tag")
def get_prompts_by_tag(
    tags: str = Query("", title="Tags", description="Comma-separated list of tags to search for"),
    service: PromptServiceInterface = Depends(get_prompt_service)):
    return service.get_prompts_by_tags(tags)


@router.get("/prompt/classification/{classification}", response_model=List[Prompt],
            summary="List Public Prompts by Classification")
def get_prompts_by_classification(classification: str, service: PromptServiceInterface = Depends(get_prompt_service)):
    # Assuming the service has a method to get prompts by classification.
    return service.get_prompts_by_classification(classification)
