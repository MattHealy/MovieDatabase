from flask import g, current_app
from flask.ext.wtf import Form
from wtforms import TextField, SubmitField
from wtforms.validators import Required 

class TitleSearchForm(Form):
    title = TextField('title', validators=[Required()])
    submit = SubmitField('Search')
