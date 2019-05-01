import unittest
import os
from config import basedir
from app.models import User, Role, Permission, AnonymousUser
from app import app, db


class UserModelTestCase(unittest.TestCase):
     def setUp(self):
         self.app = app('testing')
        self.app_context = self.app.app_context()
         self.app_context.push()
         db.create_all()
         Role.insert_roles()
    
     def tearDown(self):
         db.session.remove()
         db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='banana')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='banana')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='banana')
        self.assertTrue(u.verify_password('banana'))
        self.assertFalse(u.verify_password('nyau'))

    def test_password_salts_are_random(self):
        u = User(password='banana')
        u2 = User(password='banana')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_roles_and_permissions(self):
        Role.insert_roles()
        u = User(email='doe@example.com', password='banana')
        self.assertTrue(u.operation(Permission.WRITE_ARTICLES))
        self.assertFalse(u.operation(Permission.MODERATE_COMMENTS))

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.operation(Permission.FOLLOW))
