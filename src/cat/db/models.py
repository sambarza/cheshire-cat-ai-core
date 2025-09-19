from uuid import uuid4

from tortoise.models import Model
from tortoise import fields

# TODOV2: indexes

class Setting(Model):
    name = fields.CharField(pk=True, max_length=1000)
    value = fields.JSONField()

    class Meta:
        table = "ccat_settings"


class UserSetting(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    name = fields.CharField(max_length=1000)
    value = fields.JSONField()
    user_id = fields.UUIDField(db_index=True)

    class Meta:
        table = "ccat_user_settings"


class ChatDB(Model):
    
    id = fields.UUIDField(pk=True, default=uuid4)
    title = fields.CharField(max_length=1000)
    updated_at = fields.DatetimeField(auto_now=True)
    body = fields.JSONField()
    context = fields.ForeignKeyField('models.ContextDB', related_name='chats', db_index=True)
    user_id = fields.UUIDField(db_index=True)

    class Meta:
        table = "ccat_chats"


class ContextDB(Model):

    id = fields.UUIDField(pk=True, default=uuid4)
    title = fields.CharField(max_length=1000)
    updated_at = fields.DatetimeField(auto_now=True)
    body = fields.JSONField()
    user_id = fields.UUIDField(db_index=True)

    class Meta:
        table = "ccat_contexts"
