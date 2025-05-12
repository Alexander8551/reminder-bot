import pytest
from app import create_app
from models import db, Tag
from config import TestConfig

@pytest.fixture
def test_client():
    app = create_app(TestConfig) # Используем SQLite в памяти

    # Инициализируем базу данных только один раз
    with app.app_context():
        db.create_all()
    # Создаем тестовый клиент
    with app.test_client() as client:
        yield client
    # После всех тестов очищаем базу данных
    with app.app_context():
        db.session.remove()
        db.drop_all()

def test_create_tag(test_client):
    response = test_client.post('/tags/', json={
        'name': 'Work',
        'chat_id': 12345
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Work'
    assert data['chat_id'] == 12345

def test_get_tag(test_client):
    with test_client.application.app_context():
        tag = Tag(name='Personal', chat_id=67890)
        db.session.add(tag)
        db.session.commit()

        response = test_client.get(f'/tags/{tag.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Personal'
        assert data['chat_id'] == 67890

def test_update_tag(test_client):
    with test_client.application.app_context():
        tag = Tag(name='Old Name', chat_id=11111)
        db.session.add(tag)
        db.session.commit()

        response = test_client.put(f'/tags/{tag.id}', json={
            'name': 'New Name'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'New Name'
        assert data['chat_id'] == 11111

def test_delete_tag(test_client):
    with test_client.application.app_context():
        tag = Tag(name='To Be Deleted', chat_id=22222)
        db.session.add(tag)
        db.session.commit()

        response = test_client.delete(f'/tags/{tag.id}')
        assert response.status_code == 204
        assert db.session.get(Tag, tag.id) is None
