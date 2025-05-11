from marshmallow import Schema, fields
from models import User, Reminder, Tag

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    telegram_id = fields.Int(required=True)
    username = fields.Str()
    created_at = fields.DateTime(dump_only=True)

class TagSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    chat_id = fields.Int(required=True)

class ReminderSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    chat_id = fields.Int(required=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    event_time = fields.DateTime()
    repeat_type = fields.Str(allow_none=True)
    notification_time = fields.DateTime(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    tags = fields.Nested(TagSchema, many=True, allow_none=True)