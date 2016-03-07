from flask import render_template, flash, redirect, url_for, request, g, current_app, session, \
                  abort 
from flask.ext.login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta, date
from itsdangerous import JSONWebSignatureSerializer
from . import admin
from .. import db, lm
from ..models import User
from ..email import send_email
from .forms import TitleSearchForm
import omdb

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@admin.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@admin.route('/unconfirmed/', methods=['GET'])
@login_required
def unconfirmed():

    if g.user.is_confirmed():
        return redirect(url_for('admin.home'))

    return render_template("admin/unconfirmed.html", title='Unconfirmed Account')

@admin.route('/home/', methods=['GET','POST'])
@login_required
def home():

    if not g.user.is_confirmed():
        return redirect(url_for('admin.unconfirmed'))

    return render_template("admin/home.html", title="My Collection", subtitle="Home", movies=g.user.entries)

@admin.route('/add/', methods=['GET','POST'])
@login_required
def add_entry():

    if not g.user.is_confirmed():
        return redirect(url_for('admin.unconfirmed'))

    form = TitleSearchForm()
    movies = []

    if request.args.get('title'):

        form.title.data = request.args.get('title')
        res = omdb.search(request.args.get('title'))

        for item in res:
            if item['type'] != 'movie':
                continue
            movie = {}
            movie['title'] = item['title']
            movie['year'] = item['year']
            if item['poster'] != 'N/A':
                movie['image'] = item['poster']
            movie['imdb_id'] = item['imdb_id']
            movies.append(movie)

    return render_template("admin/add.html", form=form, title="Add Entry", subtitle="Search", movies=movies)

@admin.route('/confirmation_email/', methods=['GET'])
@login_required
def send_confirmation_email():

    if g.user.is_confirmed():
        return redirect(url_for('admin.home'))

    token = g.user.generate_token()

    send_email(g.user.email, 'Confirm Account','mail/confirm_account', user=g.user, token=token)

    flash("A confirmation email has been sent to " + g.user.email)
    return redirect(url_for('admin.unconfirmed'))

@admin.route('/confirm/<token>/', methods=['GET'])
@login_required
def confirm(token):

    if g.user.is_confirmed():
        return redirect(url_for('admin.home'))

    s = JSONWebSignatureSerializer(current_app.config['SECRET_KEY'])

    data = None

    try:
        data = s.loads(token)
    except:
        abort(404)

    if data.get('id'):
        id = data.get('id')
    else:
        id = 0

    user = User.query.get_or_404(id)

    if user.id == g.user.id:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('You have successfully confirmed your account!')
    else:
        flash('Invalid token')

    return render_template("admin/confirm.html", title='Confirm Account')

