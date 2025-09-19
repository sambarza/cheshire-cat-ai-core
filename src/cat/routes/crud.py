from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from uuid import uuid4

from tortoise.models import Model
from pydantic import BaseModel
from fastapi import APIRouter

from cat.log import log
from cat.looking_glass.stray_cat import StrayCat
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions


def create_crud(
    db_model: Model,
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

    log.critical(DBModel)
    log.warning(DBModel._meta.backward_fk_fields)
    log.warning(DBModel._meta.fk_fields)

    related_schemas = \
        list(DBModel._meta.backward_fk_fields) + \
        list(DBModel._meta.fk_fields)
        

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
        
        if restrict_by_user_id:
            q = DBModel.filter(user_id=cat.user_id)
        else:
            q = DBModel.all()
        objs = await q.order_by("-updated_at").limit(100)

        #if search:
            # TODOV2: DBModel has no .body, find a more general way to search
            # no vectors like in the 90s
        #    stmt = stmt.where(func.lower(func.cast(DBModel.body, text)).ilike(f"%{search.lower()}%"))

        log.warning(related_schemas)
        if len(related_schemas) > 0:
            await DBModel.fetch_for_list(objs, *related_schemas)
        #log.warning(objs[0].chats)
        return objs


    @router.get("/{id}", description=f"Get a {tag}")
    async def get_one(
        id: str,
        #expand: bool = Query(default=None, description="Whether to expand or not related records"),
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.READ),
    ) -> SelectSchema:
        
        if restrict_by_user_id:
            obj = await DBModel.get_or_none(id=id, user_id=cat.user_id)
        else:
            obj = await DBModel.get_or_none(id=id)
        
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found.")
        
        if len(related_schemas) > 0:
            await obj.fetch_related(*related_schemas)
        log.critical(dict(obj))
        return obj


    @router.post("", description=f"Create new {tag}")
    async def create(
        data: CreateSchema = Body(...),
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.WRITE),
    ) -> SelectSchema:
        
        if restrict_by_user_id:
            new_obj = DBModel(user_id=cat.user_id, **data.model_dump())
        else:
            new_obj = DBModel(**data.model_dump())

        await new_obj.save()
        return new_obj


    @router.put("/{id}", description=f"Edit a {tag}")
    async def edit(
        id: str,
        data: UpdateSchema = Body(...),
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.EDIT),
    ) -> SelectSchema:

        if restrict_by_user_id:
            obj = await DBModel.get_or_none(id=id, user_id=cat.user_id)
        else:
            obj = await DBModel.get_or_none(id=id)

        if obj is None:
            raise HTTPException(status_code=404, detail=f"{tag } not found.")

        obj.update_from_dict(data.model_dump())
        await obj.save()
        return obj


    @router.delete("/{id}")
    async def delete(
        id: str,
        cat: StrayCat = check_permissions(auth_resource, AuthPermission.DELETE),
    ):
        
        if restrict_by_user_id:
            obj = await DBModel.get_or_none(id=id, user_id=cat.user_id)
        else:
            obj = await DBModel.get_or_none(id=id)

        if obj is None:
            raise HTTPException(status_code=404, detail=f"{tag } not found.")
                    
        await obj.delete()


    return router