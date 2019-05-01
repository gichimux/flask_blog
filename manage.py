from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import create_app,db
from app.models import User

db = SQLAlchemy

@manager.shell
def make_shell_context():
    return dict(app = app, db = db, User = User)

if __name__ == "__main__":
    manager.run()