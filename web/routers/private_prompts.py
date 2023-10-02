from typing import List

from fastapi import APIRouter, Depends

from core.models import Prompt, User
from service.prompt_service import PromptServiceInterface
from web.dependencies import require_current_user, get_prompt_service

router = APIRouter()


@router.post("/prompt/", status_code=201, summary="Add a New Private Prompt")
async def add_prompt(prompt: Prompt,
                     service: PromptServiceInterface = Depends(get_prompt_service),
                     user: User = Depends(require_current_user)):
    return await service.create_prompt(prompt, user)


@router.delete("/prompt/{guid}", status_code=204, summary="Delete a Private Prompt by GUID")
async def delete_prompt(guid: str,
                        service: PromptServiceInterface = Depends(get_prompt_service),
                        user: User = Depends(require_current_user)):
    await service.delete_prompt(guid)
    return {}  # Return an empty response for 204 status


@router.put("/prompt/{guid}", summary="Update a Private Prompt by GUID")
async def update_prompt(guid: str, prompt: Prompt, service: PromptServiceInterface = Depends(get_prompt_service),
                        user: User = Depends(require_current_user)):
    assert guid == prompt.guid
    return await service.update_prompt(prompt)

@router.get("/prompt/", response_model=List[Prompt], summary="List all Private Prompts")
def list_prompts(skip: int = 0, limit: int = 10,
                 service: PromptServiceInterface = Depends(get_prompt_service),
                 user: User = Depends(require_current_user)):
    # Using pagination with skip and limit.
    # You can enhance this further by allowing filters like tags, authors, etc.
    return service.list_prompts()[skip: skip+limit]


@router.get("/prompt/search", response_model=List[Prompt], summary="Search Private Prompts")
async def search_prompts(query: str, service: PromptServiceInterface = Depends(get_prompt_service),
                         user: User = Depends(require_current_user)):
    return await service.search_prompts(query)


@router.get("/prompt/tags/{tag}/", response_model=List[Prompt], summary="List Private Prompts by Tag")
async def get_prompts_by_tag(tag: str, service: PromptServiceInterface = Depends(get_prompt_service),
                             user: User = Depends(require_current_user)):
    return await service.get_prompts_by_tag(tag)


@router.get("/prompt/classification/{classification}/", response_model=List[Prompt],
            summary="List Private Prompts by Classification")
async def get_prompts_by_classification(classification: str,
                                        service: PromptServiceInterface = Depends(get_prompt_service),
                                        user: User = Depends(require_current_user)):
    return await service.get_prompts_by_classification(classification)
