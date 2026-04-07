from app import app
from flask import session
from flask import render_template, redirect, url_for, request
from app.forms import CreateRecipe, SearchRecipe, CreateGroup, SearchGroup
from app import db
from app.models import Recipe, Ingredient, Group, User
import sys
from datetime import datetime

@app.route('/', methods=['GET'])
def home():
    form = SearchRecipe(request.args)
    form2 = SearchGroup(request.args)
    recipes_query = Recipe.query.filter_by(privacy_setting='public')
    groups_query = Group.query.filter_by(privacy_setting='public')
    if form.searchA.data and form.searchA.data.strip():
        recipes_query = recipes_query.filter(
            Recipe.title.ilike(f"%{form.searchA.data}%")
        )
    if form2.searchB.data and form2.searchB.data.strip():
        groups_query = groups_query.filter(
            Group.group_name.ilike(f"%{form2.searchB.data}%")
        )
    recipes = recipes_query.all()
    groups = groups_query.all()
    return render_template('index.html', recipes=recipes, groups=groups, form=form, form2=form2)



@app.route('/recipe/<int:recipe_id>', methods=['GET'])
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    ingredients = Ingredient.query.filter_by(recipe_id=recipe_id).all()
    return render_template('recipe_detail.html', recipe=recipe, ingredients=ingredients)

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
                db.session.add(i)
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

@app.route('/create-group',methods=['GET', 'POST'])
def add_group():
    form = CreateGroup()
    if form.validate_on_submit():
        # Extract values from form
        group_name = form.group_name.data
        privacy = form.privacy.data

        c = Group(group_name=group_name,privacy_setting=privacy)

        # add record to table and commit changes
        db.session.add(c)
        db.session.flush()
        db.session.commit()
        form.group_name.data=''
        form.privacy.data=''
        return redirect(url_for('add_group'))
    return render_template('create_group.html',form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        existing = User.query.filter_by(email=email).first()
        if not existing:
            new_user = User(
                email=email,
                username=username,
                password=password,
                date_joined=datetime.now().strftime("%Y-%m-%d"),
                isPending=False
            )
            db.session.add(new_user)
            db.session.commit()

            session['user'] = email
            return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user'] = user.email
            return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))
