from flask import render_template, flash, redirect, url_for, request, g, current_app, session, \
                  abort, Markup
from flask.ext.login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta, date
from itsdangerous import JSONWebSignatureSerializer
from . import admin
from .. import db, lm
from ..models import User, Entry
from ..email import send_email
from .forms import TitleSearchForm, AddEntryForm, LibrarySortForm
import omdb

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@admin.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated:
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

    movies = Entry.query.filter_by(user_id = g.user.id, wishlist = 0)

    order_by = request.args.get('order_by', 'title')

    sortform = LibrarySortForm()
    sortform.order_by.data = order_by

    if order_by == 'timestamp':
        movies = movies.order_by(Entry.timestamp)
    elif order_by == 'timestampDesc':
        movies = movies.order_by(Entry.timestamp.desc())
    elif order_by == 'year':
        movies = movies.order_by(Entry.year)
    elif order_by == 'yearDesc':
        movies = movies.order_by(Entry.year.desc())
    elif order_by == 'titleDesc':
        movies = movies.order_by(Entry.title.desc())
    else:
        movies = movies.order_by(Entry.title)

    return render_template("admin/home.html", title="My Collection", subtitle="Home", movies=movies,
                           sortform=sortform)

@admin.route('/wishlist/', methods=['GET','POST'])
@login_required
def wishlist():

    if not g.user.is_confirmed():
        return redirect(url_for('admin.unconfirmed'))

    movies = Entry.query.filter_by(user_id = g.user.id, wishlist = 1)

    order_by = request.args.get('order_by', 'title')

    sortform = LibrarySortForm()
    sortform.order_by.data = order_by

    if order_by == 'timestamp':
        movies = movies.order_by(Entry.timestamp)
    elif order_by == 'timestampDesc':
        movies = movies.order_by(Entry.timestamp.desc())
    elif order_by == 'year':
        movies = movies.order_by(Entry.year)
    elif order_by == 'yearDesc':
        movies = movies.order_by(Entry.year.desc())
    elif order_by == 'titleDesc':
        movies = movies.order_by(Entry.title.desc())
    else:
        movies = movies.order_by(Entry.title)

    return render_template("admin/home.html", title="Wishlist", subtitle="Home", movies=movies,
                           sortform=sortform)

@admin.route('/entry/add/', methods=['GET','POST'])
@login_required
def add_entry():

    if not g.user.is_confirmed():
        return redirect(url_for('admin.unconfirmed'))

    form = TitleSearchForm()
    addform = AddEntryForm()
    addform.wishlist.data = 0
    movies = []

    if request.args.get('title'):

        form.title.data = request.args.get('title')
        res = omdb.search(request.args.get('title'))

        for item in res:
            movie = {}
            movie['title'] = item['title']
            movie['year'] = item['year']
            if item['poster'] != 'N/A':
                movie['image'] = item['poster']
            movie['imdb_id'] = item['imdb_id']
            movies.append(movie)

    return render_template("admin/add.html", form=form, title="Add Entry", subtitle="Search", \
                           movies=movies, addform = addform)

@admin.route('/wishlist/add/', methods=['GET','POST'])
@login_required
def add_wishlist():

    if not g.user.is_confirmed():
        return redirect(url_for('admin.unconfirmed'))

    form = TitleSearchForm()
    addform = AddEntryForm()
    addform.wishlist.data = 1
    movies = []

    if request.args.get('title'):

        form.title.data = request.args.get('title')
        res = omdb.search(request.args.get('title'))

        for item in res:
            movie = {}
            movie['title'] = item['title']
            movie['year'] = item['year']
            if item['poster'] != 'N/A':
                movie['image'] = item['poster']
            movie['imdb_id'] = item['imdb_id']
            movies.append(movie)

    return render_template("admin/add.html", form=form, title="Add to Wishlist", subtitle="Search", \
                           movies=movies, addform = addform)

@admin.route('/entry/add/<imdb_id>/', methods=['POST'])
@login_required
def submit_entry(imdb_id):

    if not g.user.is_confirmed():
        return redirect(url_for('admin.unconfirmed'))

    form = AddEntryForm()

    if form.validate_on_submit():

        res = omdb.imdbid(imdb_id)

        wishlist = form.wishlist.data
        entry = Entry.query.filter_by(user_id = g.user.id, imdb_id = imdb_id).first()

        if entry:
            flash('This entry already exists in your collection')
            return redirect(url_for('admin.home'))

        entry = Entry(user_id = g.user.id, timestamp = datetime.utcnow(), wishlist = wishlist)

        title = res['title']
        entry.title = res['title']
        entry.year = res['year']
        if res['poster'] != 'N/A':
            entry.image = res['poster']

        entry.imdb_id = res['imdb_id']

        db.session.add(entry)
        db.session.commit()

        flash(Markup('Entry added successfully. <strong><a href="' + url_for('admin.add_entry') + '">Add another?</a></strong>'))

        if wishlist:
            return redirect(url_for('admin.wishlist'))
        else:
            return redirect(url_for('admin.home'))

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

