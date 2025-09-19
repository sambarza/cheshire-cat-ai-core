import time
from datetime import datetime
from uuid import uuid4

from tortoise.models import Model
from tortoise import fields

class Tournament(Model):
    # Defining `id` field is optional, it will be defined automatically
    # if you haven't done it yourself
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)


class Event(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    # References to other models are defined in format
    # "{app_name}.{model_name}" - where {app_name} is defined in the tortoise config
    tournament = fields.ForeignKeyField('models.Tournament', related_name='events')
    participants = fields.ManyToManyField('models.Team', related_name='events', through='event_team')


class Team(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=1000)


class Setting(Model):
    name = fields.CharField(pk=True, max_length=1000)
    value = fields.JSONField()


class ChatDB(Model):
    
    id = fields.UUIDField(pk=True, default=uuid4)
    title = fields.CharField(max_length=1000)
    updated_at = fields.DatetimeField(auto_now=True)
    body = fields.JSONField()
    context = fields.ForeignKeyField('models.ContextDB', related_name='chats')
    user_id = fields.UUIDField()


class ContextDB(Model):

    id = fields.UUIDField(pk=True, default=uuid4)
    title = fields.CharField(max_length=1000)
    updated_at = fields.DatetimeField(auto_now=True)
    body = fields.JSONField()
    user_id = fields.UUIDField()
