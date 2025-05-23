import pytest
from app import create_app
from models import db, Reminder, User
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
		
@pytest.fixture
def create_user(test_client):  # Передаем test_client, чтобы использовать контекст приложения
	with test_client.application.app_context(): 
		user = User(telegram_id=123456789, username='testuser')
		db.session.add(user)
		db.session.commit()
		# Привязываем объект user к текущей сессии
		return user

def test_create_reminder(test_client, create_user):
	with test_client.application.app_context():
		user = db.session.merge(create_user)
		response = test_client.post('/reminders/', json={
			'user_id': user.id,
			'chat_id': 12345,
			'title': 'Test Reminder',
		})
		assert response.status_code == 201
		data = response.get_json()
		assert data['title'] == 'Test Reminder'

def test_get_reminder(test_client, create_user):
	# Предварительно создаем напоминание внутри контекста приложения
	with test_client.application.app_context():
		user = db.session.merge(create_user)
		reminder = Reminder(user_id=user.id, chat_id=12345, title='Test Reminder')
		db.session.add(reminder)
		db.session.commit()

		# Выполняем запрос на получение созданного напоминания
		response = test_client.get(f'/reminders/{reminder.id}')
		assert response.status_code == 200
		data = response.get_json()
		assert data['title'] == 'Test Reminder'

def test_update_reminder(test_client, create_user):
	with test_client.application.app_context():
		user = db.session.merge(create_user)
		reminder = Reminder(user_id=user.id, chat_id=12345, title='Old Title')
		db.session.add(reminder)
		db.session.commit()

		response = test_client.put(f'/reminders/{reminder.id}', json={
			'title': 'New Title'
		})
		assert response.status_code == 200
		data = response.get_json()
		assert data['title'] == 'New Title'

def test_delete_reminder(test_client, create_user):
	with test_client.application.app_context():
		user = db.session.merge(create_user)

		# Создаём напоминание от имени user
		reminder = Reminder(user_id=user.id, chat_id=12345, title='Test Reminder')
		db.session.add(reminder)
		db.session.commit()

		# 1. Удаление с правильным user_id
		response = test_client.delete(
			f'/reminders/{reminder.id}?user_id={user.id}'
		)
		assert response.status_code == 204
		assert db.session.get(Reminder, reminder.id) is None

		# 2. Ошибка если user_id не передан
		# Снова создаём напоминание
		reminder2 = Reminder(user_id=user.id, chat_id=12345, title='Test Reminder 2')
		db.session.add(reminder2)
		db.session.commit()

		response = test_client.delete(f'/reminders/{reminder2.id}')
		assert response.status_code == 400
		assert response.get_json()['error'] == "user_id is required"

		# 3. Ошибка если user_id не совпадает
		# Создаём "чужого" пользователя
		other_user = User(telegram_id=987654321, username='otheruser')
		db.session.add(other_user)
		db.session.commit()

		response = test_client.delete(
			f'/reminders/{reminder2.id}?user_id={other_user.id}'
		)
		assert response.status_code == 403
		assert "Вы не владелец" in response.get_json()['error']
