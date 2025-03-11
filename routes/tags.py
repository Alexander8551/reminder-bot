from flask import Blueprint, request, jsonify
from models import db, Tag
from schemas import TagSchema

bp = Blueprint('tags_bp', __name__, url_prefix='/tags')

@bp.route('/', methods=['POST'])
def create_tag():
    data = request.get_json()
    schema = TagSchema()
    tag_data = schema.load(data)
    tag = Tag(**tag_data)
    db.session.add(tag)
    db.session.commit()
    return schema.dump(tag), 201

@bp.route('/<int:id>', methods=['GET'])
def get_tag(id):
    tag = Tag.query.get_or_404(id)
    schema = TagSchema()
    return schema.dump(tag)

@bp.route('/<int:id>', methods=['PUT'])
def update_tag(id):
    tag = Tag.query.get_or_404(id)
    data = request.get_json()
    schema = TagSchema()
    tag_data = schema.load(data, partial=True)
    for key, value in tag_data.items():
        setattr(tag, key, value)
    db.session.commit()
    return schema.dump(tag)

@bp.route('/<int:id>', methods=['DELETE'])
def delete_tag(id):
    tag = Tag.query.get_or_404(id)
    db.session.delete(tag)
    db.session.commit()
    return '', 204
