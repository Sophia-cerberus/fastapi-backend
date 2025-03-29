from typing import Any
import uuid

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Model,
)


async def sync_provider_models(
    session: AsyncSession, provider_id: uuid.UUID, config_models: list[dict[str, Any]]
) -> list[Model]:
    """
    同步配置文件中的模型到数据库
    """
    # 获取现有模型
    statement = select(Model).where(Model.provider_id == provider_id)
    existing_models = await session.scalars(statement)

    existing_model_names = {model.ai_model_name for model in existing_models}

    instance = []

    for config_model in config_models:
        model_name = config_model["name"]

        # 准备模型元数据
        meta_ = {}
        if "dimension" in config_model:
            meta_["dimension"] = config_model["dimension"]

        if model_name in existing_model_names:
            # 更新现有模型
            model = next(m for m in existing_models if m.ai_model_name == model_name)
            model.categories = config_model["categories"]
            model.capabilities = config_model.get("capabilities", [])
            model.meta_ = meta_
        else:
            # 创建新模型
            model = Model(
                ai_model_name=model_name,
                provider_id=provider_id,
                categories=config_model["categories"],
                capabilities=config_model.get("capabilities", []),
                meta=meta_,
            )
            session.add(model)
        instance.append(model)

    await session.commit()
    return instance