from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from uuid import uuid4

from pydantic import BaseModel
from fastapi import APIRouter

from cat.log import log
from cat.looking_glass.stray_cat import StrayCat
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions


def get_relationships(db_model):
    """
    Return a dict of relationship info for a SQLAlchemy model.
    """
    #mapper = inspect(db_model)
    relationships = {}

    #for rel in mapper.relationships:
    #    relationships[rel.key] = {
    #        "target": rel.mapper.class_.__name__,
    #        "direction": rel.direction.name,
    #        "uselist": rel.uselist,
    #        "local_cols": [c.name for c in rel.local_columns],
    #        "remote_cols": [c.name for c in rel.remote_side],
    #    }

    return relationships


def create_crud(
    db_model,
    prefix: str,
    tag: str,
    auth_resource: AuthResource,
    select_schema: BaseModel,
    create_schema: BaseModel,
    update_schema: BaseModel,
    restrict_by_user_id: bool = False
) -> APIRouter:

    DBModel = db_model
    SelectSchema = select_schema
    CreateSchema = create_schema
    UpdateSchema = update_schema

    relationships = get_relationships(DBModel)
    
    router = APIRouter(
        prefix=prefix,
        tags=[tag]
    )

    @router.get("", description=f"List and search {tag}")
    async def get_list(
        search: Optional[str] = Query(None, description="Search query"),
        # TODOV2: pagination
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.LIST),
    ) -> List[SelectSchema]:

        stmt = select(DBModel).where(DBModel.user_id == cat.user_id)
        if restrict_by_user_id:
            stmt = stmt.where(DBModel.user_id == cat.user_id)

        if search:
            # TODOV2: DBModel has no .body, find a more general way to search
            # no vectors like in the 90s
            stmt = stmt.where(func.lower(func.cast(DBModel.body, text)).ilike(f"%{search.lower()}%"))

        stmt = stmt.order_by(desc(DBModel.updated_at)).limit(100)

        result = await db.execute(stmt)
        objs = result.scalars().all()
        return objs


    @router.get("/{id}", description=f"Get a {tag}")
    async def get_one(
        id: str,
        expand: str = Query(default=None, description=f"Which relationship to expand. Avilable: {", ".join(list(relationships.keys()))}"),
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.READ),
    ) -> SelectSchema:

        stmt = select(DBModel).where(DBModel.id == id)
        # TODOV2: test another user cannot access
        if restrict_by_user_id:
            stmt = stmt.where(DBModel.user_id == cat.user_id)

        expand_list = expand.split(",") if expand else []
        for rel in expand_list:
            if rel in relationships.keys():
                rel_attr = getattr(DBModel, rel)
                stmt = stmt.options(joinedload(rel_attr))

        result = await db.execute(stmt)
        result = result.scalar_one_or_none()
        if result is None:
            raise HTTPException(status_code=404, detail="Not found.")
        log.warning("Always expanding :(")
        return result


    @router.post("", description=f"Create new {tag}")
    async def create(
        data: CreateSchema = Body(...),
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.WRITE),
    ) -> SelectSchema:
        
        if restrict_by_user_id:
            new_obj = DBModel(user_id=cat.user_id, **data.model_dump())
        else:
            new_obj = DBModel(**data.model_dump())

        db.add(new_obj)
        await db.flush()
        await db.refresh(new_obj)
        return new_obj


    @router.put("/{id}", description=f"Edit a {tag}")
    async def edit(
        id: str,
        data: UpdateSchema = Body(...),
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.EDIT),
    ) -> SelectSchema:

        stmt = update(DBModel).where(DBModel.id == id)
        if restrict_by_user_id:
            stmt = stmt.where(DBModel.user_id == cat.user_id)
        
        stmt = stmt.values(**data.model_dump(exclude_unset=True))\
            .execution_options(synchronize_session="fetch")

        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"{tag} not found")

        q = select(DBModel).where(DBModel.id == id)
        updated_obj = (await db.execute(q)).scalar_one()
        return updated_obj


    @router.delete("/{id}")
    async def delete(
        id: str,
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.DELETE),
    ):
        stmt = select(DBModel).where(DBModel.id == id)
        if restrict_by_user_id:
            stmt = stmt.where(DBModel.user_id == cat.user_id)

        result = await db.execute(stmt)
        chat = result.scalar_one_or_none()
        if chat is None:
            raise HTTPException(status_code=404, detail=f"{tag } not found.")

        await db.delete(chat)

    return router