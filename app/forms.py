from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, RadioField, TextAreaField, FieldList, FormField
from wtforms.validators import DataRequired, Optional, NumberRange, InputRequired
from wtforms import Form

class IngredientForm(Form):
    num= IntegerField("Quantity:", validators=[Optional(), NumberRange(min=1, message="Must be at least 1")])
    ingredient_name = StringField("Ingredient:", validators=[Optional()])
    unit = StringField("Unit:", validators=[Optional()])

class CreateRecipe(FlaskForm):
    title = StringField("Recipe Title:",validators=[DataRequired()])
    prep_time = IntegerField("Prep Time (minutes):",validators=[InputRequired(), NumberRange(min=0, message="Cannot be negative")])
    cook_time = IntegerField("Cook Time (minutes):",validators=[InputRequired(), NumberRange(min=0, message="Cannot be negative")])
    body = TextAreaField("Instructions:",validators=[DataRequired()])
    num_serves = IntegerField("Number of Servings:",validators=[DataRequired(), NumberRange(min=1, message="Must be at least 1")])
    ingredients = FieldList(FormField(IngredientForm), min_entries=1)
    privacy = RadioField("Privacy Settings:", choices = [("public", "Visible to Everyone"), ("private", "Visible to Group Only"), ("unlisted", "Visible to Me Only")],validators=[DataRequired()])
    category = RadioField("Category:", choices = [("appetizer", "Appetizer"), ("breakfast", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner"), ("dessert", "Dessert")],validators=[DataRequired()])
    submit = SubmitField('Create Recipe!')

class SearchRecipe(FlaskForm):
    search = StringField("Search recipes:", validators=[Optional()])
    submit = SubmitField('Search')

class CreateGroup(FlaskForm):
    group_name = StringField("Group Name:",validators=[DataRequired()])
    privacy = RadioField("Visibility", choices = [("public","Visible to everyone"),("private","Visble to members")],validators=[DataRequired()])
    submit = SubmitField("Create Group")
