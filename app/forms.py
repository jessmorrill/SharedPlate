from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired

class AddForm(FlaskForm):
    city = StringField('City:', validators=[DataRequired()])
    population = IntegerField('Population: ', validators=[DataRequired()])
    submit = SubmitField('Save')

class DeleteForm(FlaskForm):
    city = StringField('City:', validators=[DataRequired()])
    submit = SubmitField('Delete')

class SearchForm(FlaskForm):
    city = StringField('City:', validators=[DataRequired()])
    submit = SubmitField('Search')

class FilterForm(FlaskForm):
    population = IntegerField('Minimum Population:' ,validators=[DataRequired()])
    submit = SubmitField('Search')
