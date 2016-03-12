from app import db
from flask import current_app, flash, url_for
from itsdangerous import JSONWebSignatureSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .email import send_email

import os.path
import pytz

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index = True)
    last_seen = db.Column(db.DateTime)
    first_login = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean)

    entries = db.relationship('Entry', backref='user', lazy='dynamic', cascade="all, delete",
                              order_by="Entry.title")

    def is_admin(self):
        if str(self.id) in current_app.config['ADMINS']:
            return True
        else:
            return False

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return True

    def is_confirmed(self):
        return self.confirmed

    def get_id(self):
        return str(self.id)

    def generate_token(self):
        s = JSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': self.id})

    def __repr__(self):
        return '<User %r %r>' % (self.first_name, self.last_name)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def on_changed_email(target, value, oldvalue, initiator):
        if value != oldvalue and target.confirmed:
            send_email(value, 'Confirm Account','mail/confirm_account', user=target, token=target.generate_token())
            flash("A confirmation email has been sent to " + value)
            target.confirmed = False

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime)
    title = db.Column(db.String(64))
    imdb_id = db.Column(db.String(20))
    year = db.Column(db.Integer)
    image = db.Column(db.String(256))
    wishlist = db.Column(db.Boolean)

    def __repr__(self):
        return '<Entry %r (%r)>' % (self.title, self.year)
