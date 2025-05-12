import pytest
from app import create_app
from models import db, User
from config import TestConfig

@pytest.fixture
def test_client():
    app = create_app(TestConfig) # Используем SQLite в памяти

    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove()
        db.drop_all()

def test_create_user(test_client):
    response = test_client.post('/users/', json={
        'telegram_id': 123456789,
        'username': 'testuser'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['telegram_id'] == 123456789
    assert data['username'] == 'testuser'

def test_get_user(test_client):
    with test_client.application.app_context():
        user = User(telegram_id=123456789, username='testuser')
        db.session.add(user)
        db.session.commit()

        response = test_client.get(f'/users/{user.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['telegram_id'] == 123456789
        assert data['username'] == 'testuser'

def test_update_user(test_client):
    with test_client.application.app_context():
        user = User(telegram_id=123456789, username='olduser')
        db.session.add(user)
        db.session.commit()

        response = test_client.put(f'/users/{user.id}', json={
            'username': 'newuser'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == 'newuser'

def test_delete_user(test_client):
    with test_client.application.app_context():
        user = User(telegram_id=123456789, username='testuser')
        db.session.add(user)
        db.session.commit()

        response = test_client.delete(f'/users/{user.id}')
        assert response.status_code == 204
        assert db.session.get(User, user.id) is None
