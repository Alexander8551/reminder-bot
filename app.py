from flask import Flask
from config import Config
from models import db
from routes import users, reminders, tags

def create_app(config_object=None):
    app = Flask(__name__)
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Регистрация блюпринтов
    app.register_blueprint(users.bp)
    app.register_blueprint(reminders.bp)
    app.register_blueprint(tags.bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)