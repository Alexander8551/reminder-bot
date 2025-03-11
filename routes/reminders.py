from flask import Blueprint, request, jsonify
from models import db, Reminder, Tag
from schemas import ReminderSchema

bp = Blueprint('reminders_bp', __name__, url_prefix='/reminders')

@bp.route('/', methods=['POST'])
def create_reminder():
    data = request.get_json()
    schema = ReminderSchema()
    reminder_data = schema.load(data)
    reminder = Reminder(**reminder_data)
    db.session.add(reminder)
    db.session.commit()
    return schema.dump(reminder), 201

@bp.route('/<int:id>', methods=['GET'])
def get_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    schema = ReminderSchema()
    return schema.dump(reminder)

@bp.route('/<int:id>', methods=['PUT'])
def update_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    data = request.get_json()
    schema = ReminderSchema()
    reminder_data = schema.load(data, partial=True)
    for key, value in reminder_data.items():
        setattr(reminder, key, value)
    db.session.commit()
    return schema.dump(reminder)

@bp.route('/<int:id>', methods=['DELETE'])
def delete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    db.session.delete(reminder)
    db.session.commit()
    return '', 204