from flask import Blueprint, request, jsonify
from models import db, User
from schemas import UserSchema

bp = Blueprint('users_bp', __name__, url_prefix='/users')

@bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    schema = UserSchema()
    user_data = schema.load(data)
    user = User(**user_data)
    db.session.add(user)
    db.session.commit()
    return schema.dump(user), 201

@bp.route('/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    schema = UserSchema()
    return schema.dump(user)

@bp.route('/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    schema = UserSchema()
    user_data = schema.load(data, partial=True)
    for key, value in user_data.items():
        setattr(user, key, value)
    db.session.commit()
    return schema.dump(user)

@bp.route('/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
