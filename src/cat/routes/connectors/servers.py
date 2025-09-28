from typing import List
from pydantic import BaseModel

from fastapi import APIRouter
from cat.auth.permissions import AuthPermission, AuthResource, check_permissions


router = APIRouter(prefix="/connectors", tags=["MCP"])

