import datetime
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app, request, url_for
from hashlib import md5
from werkzeug.security import generate_password_hash, check_password_hash
from markdown import markdown
import bleach
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from .errors import ValidationError
from . import db, lm, whooshee

class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    followed = db.relationship('Follow',foreign_keys = [Follow.follower_id], backref = db.backref('follower', lazy='joined'),lazy = 'dynamic',cascade = 'all, delete-orphan')
    followers = db.relationship('Follow',foreign_keys=[Follow.followed_id],backref=db.backref('followed', lazy='joined'),lazy='dynamic',cascade='all, delete-orphan')