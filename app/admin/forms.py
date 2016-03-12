from flask import g, current_app
from flask.ext.wtf import Form
from wtforms import TextField, SubmitField, SelectField, HiddenField
from wtforms.validators import Required 

class TitleSearchForm(Form):
    title = TextField('title', validators=[Required()])
    submit = SubmitField('Search')

class AddEntryForm(Form):
    wishlist = HiddenField('wishlist')
    submit = SubmitField('Add')

class LibrarySortForm(Form):
    order_by = SelectField('Order By', choices=[
        ("title","Order by Title"),
        ("titleDesc","Order by Title (desc)"),
        ("timestamp","Order by Date Added"),
        ("timestampDesc","Order by Date Added (desc)")])
