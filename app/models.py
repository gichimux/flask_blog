import bleach
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from hashlib import md5
import datetime
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from markdown import markdown
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

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMINMAIL']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def operation(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.operation(Permission.ADMINISTER)

    def follow(self, user):
        if not self.is_following(user):
            follower = Follow(follower=self, followed=user)
            db.session.add(follower)

     def unfollow(self, user):
            follower =self.followed.filter_by(followed_id=user.id).first()
        if follower:
            db.session.delete(follower)
    
    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None
    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id==Post.author_id).filter(
            Follow.follower_id==self.id)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def gravatar(self, size):
        return 'http://www.gravatar.com/avatar/' + md5(self.email.encode('utf-8')).hexdigest() + '?d=mm&s=' + str(size)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['ECRET_KEY'],expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id, _external=True),
            'nickname': self.nickname,
            'last_seen': self.last_seen,
            'posts': url_for('api.get_user_posts', id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts', id=self.id, _external=True),
            'post_count': self.posts.count()
        }
        return json_user 

    def __repr__(self):
        return '<User %r>' % (self.nickname)    

@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))    

@whooshee.register_model('title','body')
class Blog_post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(64))
    disabled = db.Column(db.Boolean)
    body = db.Column(db.Text)
    view_num = db.Column(db.Integer, default=0)
    body_html = db.Column(db.Text)
    draft = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    like_num = db.relationship('Like', backref='blog_post', lazy='dynamic')
    comments = db.relationship('Comment', backref='blog_post', lazy='dynamic')

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow())
    disabled = db.Column(db.Boolean)
    comment_type = db.Column(db.String(64), default='comment')
    reply_to = db.Column(db.String(128), default='notReply')
    unread = db.Column(db.Boolean)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    notice = db.Column(db.String(25))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow())

    def __repr__(self):
        return '<Admin %r>' % (self.notice)

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    unread = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow())

    liker_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    users = db.relationship('User', backref = 'role', lazy='dynamic')

