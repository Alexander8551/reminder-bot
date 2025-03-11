from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, nullable=False)
    username = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reminders = db.relationship('Reminder', backref='user', lazy=True)

class Reminder(db.Model):
    __tablename__ = 'Reminder'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    chat_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_time = db.Column(db.DateTime)
    repeat_type = db.Column(db.String(50))
    notification_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tags = db.relationship('Tag', secondary='ReminderTag', backref='reminders')

class Tag(db.Model):
    __tablename__ = 'Tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    chat_id = db.Column(db.Integer, nullable=False)

class ReminderTag(db.Model):
    __tablename__ = 'ReminderTag'
    id = db.Column(db.Integer, primary_key=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('Reminder.id', ondelete='CASCADE'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('Tag.id'), nullable=False)