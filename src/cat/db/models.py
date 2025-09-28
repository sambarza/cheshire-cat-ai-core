
from uuid import uuid4

from tortoise import Tortoise, fields
from tortoise.models import Model


##############################
### globally scoped tables ###
########################## ###

class SettingDB(Model):
    name = fields.CharField(pk=True, max_length=1000)
    value = fields.JSONField()
    class Meta:
        table = "ccat_global_settings"

"""
class PluginDB(Model):
    name = fields.CharField(pk=True, max_length=1000)
    active = fields.BooleanField(default=True)
    settings = fields.JSONField()
    class Meta:
        table = "ccat_global_plugins"
"""

##########################
### user scoped tables ###
##########################

class UserScopedModelDB(Model):
    id = fields.UUIDField(pk=True, default=uuid4)
    name = fields.CharField(max_length=1000)
    updated_at = fields.DatetimeField(auto_now=True)
    user_id = fields.UUIDField(db_index=True)
    class Meta:
        abstract = True

class UserSettingDB(UserScopedModelDB):
    value = fields.JSONField()
    class Meta:
        table = "ccat_settings"

class ConnectorDB(UserScopedModelDB):
    url = fields.CharField(max_length=1000)
    active = fields.BooleanField(default=True)
    secret = fields.JSONField() # TODOV2: should be encrypted, also plugin settings
    manifest = fields.JSONField(default={})

    class Meta:
        table = "ccat_connectors"

class ContextDB(UserScopedModelDB):
    instructions = fields.TextField()
    resources = fields.JSONField()

    class Meta:
        table = "ccat_contexts"

class ChatDB(UserScopedModelDB):
    messages = fields.JSONField()
    context = fields.ForeignKeyField(
        'models.ContextDB', related_name='chats', db_index=True
    )
    
    class Meta:
        table = "ccat_chats"



# necessary for relationships
Tortoise.init_models(["cat.db.models"], "models")