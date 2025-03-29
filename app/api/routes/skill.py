from typing import Any, List
import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import or_, select

from app.api.dependencies import SessionDep, CurrentInstanceSkill, CurrentTeamAndUser, ValidateUpdateInSkill
from app.api.models import (
    Message,
    Skill,
    SkillCreate,
    SkillOut,
    SkillUpdate,
    Team
)
# from app.core.tools.api_tool import ToolDefinition
# from app.core.tools.tool_invoker import ToolInvokeResponse, invoke_tool

from langchain_mcp_adapters.client import MultiServerMCPClient, BaseTool

from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import Page

from fastapi_filter import FilterDepends

from ..filters import SkillFilter


router = APIRouter(
    prefix="/skill", tags=["skill"], 
)


@router.get("/", response_model=Page[SkillOut])
async def read_skills(
    session: SessionDep, 
    current_team_and_user: CurrentTeamAndUser,
    skill_filter: SkillFilter = FilterDepends(SkillFilter)
) -> Any:
    """
    Retrieve skills
    """
    statement = select(Skill).where(Skill.team_id == current_team_and_user.team.id)
    if not current_team_and_user.user.is_superuser:
        statement = statement.join(Team).where(
            or_(
                Skill.owner_id == current_team_and_user.user.id, 
                Skill.is_public == True,
                Team.owner_id == current_team_and_user.user.id
            )
        )

    statement = skill_filter.filter(statement)
    statement = skill_filter.sort(statement)
    return await paginate(session, statement)


@router.get("/{id}", response_model=SkillOut)
def read_skill(skill: CurrentInstanceSkill) -> Skill:
    """
    Get skill by ID.
    """
    return skill


@router.post("/", response_model=SkillOut)
async def create_skill(
    *,
    session: SessionDep,
    current_team_and_user: CurrentTeamAndUser,
    skill_in: SkillCreate,
) -> Any:
    """
    Create new skill.
    """
    skill = Skill.model_validate(skill_in, update={
        "owner_id": current_team_and_user.user.id,
        "team_id": current_team_and_user.team.id
    })
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return skill


@router.put("/{id}", response_model=SkillOut)
async def update_skill(
    *,
    session: SessionDep,
    skill: ValidateUpdateInSkill,
    skill_in: SkillUpdate,
) -> Any:
    """
    Update a skill.
    """
    skill.sqlmodel_update(skill_in, update={"credentials": skill_in.credentials or {}})
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return skill


@router.delete("/{id}")
async def delete_skill(session: SessionDep, skill: CurrentInstanceSkill) -> Any:
    """
    Delete a skill.
    """
    if skill.managed:
        raise HTTPException(status_code=400, detail="Cannot delete managed skills")
    
    await session.delete(skill)
    await session.commit()
    return Message(message="Skill deleted successfully")


# @router.post("/invoke-tool")
# def invoke_tools(tool_name: str, args: dict) -> ToolInvokeResponse:
#     """
#     Invoke a tool by name with the provided arguments.
#     """
#     result = invoke_tool(tool_name, args)  # 调用工具函数
#     return result  # 直接返回自定义响应模型


@router.patch("/{id}/credentials", response_model=SkillOut)
async def update_credentials(
    *,
    session: SessionDep,
    skill: ValidateUpdateInSkill,
    credentials: dict[str, dict[str, Any]],
) -> Any:
    """
    Update a skill's credentials.
    """
    skill.credentials = credentials or {}
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return skill


@router.post("/mcp/tools", response_model=List[BaseTool])
async def get_mcp_tools(mcp_config: dict[str, Any]) -> List[BaseTool]:
    async with MultiServerMCPClient(mcp_config) as client:
        return client.get_tools()