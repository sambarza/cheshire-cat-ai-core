from uuid import uuid4

from tortoise.models import Model
from tortoise import fields

# TODOV2: indexes

class SettingDB(Model):
    name = fields.CharField(pk=True, max_length=1000)
    value = fields.JSONField()
    class Meta:
        table = "ccat_global_settings"

###########################
### user scoped records ###
###########################

class BaseDBModel(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    name = fields.CharField(max_length=1000)
    updated_at = fields.DatetimeField(auto_now=True)
    user_id = fields.UUIDField(db_index=True)
    class Meta:
        abstract = True

class UserSettingDB(BaseDBModel):
    value = fields.JSONField()
    class Meta:
        table = "ccat_settings"

class ChatDB(BaseDBModel):
    messages = fields.JSONField()
    context = fields.ForeignKeyField(
        'models.ContextDB', related_name='chats', db_index=True
    )
    class Meta:
        table = "ccat_chats"

class ContextDB(BaseDBModel):
    instructions = fields.TextField()
    resources = fields.JSONField()
    class Meta:
        table = "ccat_contexts"
