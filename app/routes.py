from app import app
from flask import render_template, redirect, url_for, request
from app.forms import CreateRecipe, SearchRecipe
from app import db
from app.models import Recipe, Ingredient
import sys
from datetime import datetime

@app.route('/', methods=['GET'])
def home():
    form = SearchRecipe(request.args)
    recipes_query = Recipe.query.filter_by(privacy_setting='public')
    if form.search.data and form.search.data.strip():
        recipes_query = recipes_query.filter(Recipe.title.ilike(f"%{form.search.data}%"))
    recipes = recipes_query.all()
    return render_template('index.html', recipes=recipes, form=form)

@app.route('/create-recipe', methods=['GET', 'POST'])
def add_recipe():
    form = CreateRecipe()
    if form.validate_on_submit():
        # Extract values from form
        title=form.title.data
        prep_time = form.prep_time.data
        cook_time = form.cook_time.data
        body = form.body.data
        num_serves = form.num_serves.data
        privacy = form.privacy.data
        category = form.category.data
        
        c = Recipe(user_email="placeholder",group_id=1, title=title, prep_time=prep_time, cook_time=cook_time, body=body, category=category,num_serves=num_serves, privacy_setting=privacy, is_validated=True, date_posted=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # add record to table and commit changes
        db.session.add(c)
        db.session.flush()
        for ingredient in form.ingredients.data:
            if ingredient['ingredient_name']:
                i = Ingredient(recipe_id=c.id, name=ingredient['ingredient_name'], num=ingredient['num'], units=ingredient['unit'])
        db.session.commit()
        form.title.data=''
        form.prep_time.data=''
        form.cook_time.data=''
        form.body.data=''
        form.num_serves.data=''
        form.privacy.data=''
        form.category.data=''
        return redirect(url_for('add_recipe'))
    return render_template('add.html', form=form)
