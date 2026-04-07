from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, RadioField, TextAreaField, FieldList, FormField
from wtforms.validators import DataRequired, Optional
from wtforms import Form

class IngredientForm(Form):
    num= IntegerField("Quantity:", validators=[Optional()])
    ingredient_name = StringField("Name:", validators=[Optional()])
    unit = StringField("Unit:", validators=[Optional()])

class CreateRecipe(FlaskForm):
    title = StringField("Recipe Title:",validators=[DataRequired()])
    prep_time = IntegerField("Prep Time (minutes):",validators=[DataRequired()])
    cook_time = IntegerField("Cook Time (minutes):",validators=[DataRequired()])
    body = TextAreaField("Instructions:",validators=[DataRequired()])
    num_serves = IntegerField("Number of Servings:",validators=[DataRequired()])
    ingredients = FieldList(FormField(IngredientForm), min_entries=1)
    privacy = RadioField("Privacy Settings:", choices = [("public", "Visible to Everyone"), ("private", "Visible to Group Only"), ("unlisted", "Visible to Me Only")],validators=[DataRequired()])
    category = RadioField("Category:", choices = [("appetizer", "Appetizer"), ("breakfast", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner"), ("dessert", "Dessert")],validators=[DataRequired()])
    submit = SubmitField('Create Recipe!')

class SearchRecipe(FlaskForm):
    search = StringField("Search recipes:", validators=[Optional()])
    submit = SubmitField('Search')
