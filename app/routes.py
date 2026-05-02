from app import app, db, mail
from flask import session, render_template, redirect, url_for, request
from flask_mail import Message
from app.forms import CreateRecipe, SearchRecipe, CreateGroup, SearchGroup
from app.models import Recipe, Ingredient, Group, User, Group_Membership
from datetime import datetime
import random


def get_current_user():
    email = session.get('user')
    if email:
        return User.query.filter_by(email=email).first()
    return None


@app.context_processor
def inject_current_user():
    email = session.get('user')
    if email:
        user = User.query.filter_by(email=email).first()
        return {'current_user': user}
    return {'current_user': None}


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
        title = form.title.data
        prep_time = form.prep_time.data
        cook_time = form.cook_time.data
        body = form.body.data
        num_serves = form.num_serves.data
        privacy = form.privacy.data
        category = form.category.data

        c = Recipe(
            user_email=session.get('user'),
            group_id=1,
            title=title,
            prep_time=prep_time,
            cook_time=cook_time,
            body=body,
            category=category,
            num_serves=num_serves,
            privacy_setting=privacy,
            is_validated=True,
            date_posted=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(c)
        db.session.flush()
        for ingredient in form.ingredients.data:
            if ingredient['ingredient_name']:
                i = Ingredient(
                    recipe_id=c.id,
                    name=ingredient['ingredient_name'],
                    num=ingredient['num'],
                    units=ingredient['unit']
                )
                db.session.add(i)
        db.session.commit()
        return redirect(url_for('add_recipe'))
    return render_template('add.html', form=form)


@app.route('/create-group', methods=['GET', 'POST'])
def add_group():
    form = CreateGroup()
    if form.validate_on_submit():
        group_name = form.group_name.data
        privacy = form.privacy.data
        c = Group(group_name=group_name, privacy_setting=privacy)
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('add_group'))
    return render_template('create_group.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        existing = User.query.filter_by(email=email).first()
        if not existing:
            code = str(random.randint(100000, 999999))

            new_user = User(
                email=email,
                username=username,
                password=password,
                date_joined=datetime.now().strftime("%Y-%m-%d"),
                isPending=True
            )
            db.session.add(new_user)
            db.session.commit()

            session['user'] = email
            session['verify_code'] = code

            msg = Message('Your verification code', recipients=[email])
            msg.body = f'Your SharedPlate verification code is: {code}'
            mail.send(msg)

            return redirect(url_for('verify'))

    return render_template('register.html')


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        entered = request.form.get('code')
        if entered == session.get('verify_code'):
            user = User.query.filter_by(email=session.get('user')).first()
            if user:
                user.isPending = False
                db.session.commit()
                session.pop('verify_code', None)
                return redirect(url_for('home'))
        else:
            return render_template('verify.html', error='Incorrect code, try again.')
    return render_template('verify.html', error=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, password=password).first()
        if user and not user.isPending:
            session['user'] = user.email
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))
  
@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    recipes = Recipe.query.filter_by(user_email=user.email).all()
    memberships = Group_Membership.query.filter_by(user_email=user.email).all()
    groups = [m.group for m in memberships]
    return render_template('dashboard.html', user=user, recipes=recipes, groups=groups)

@app.route('/group/<int:group_id>-<string:group_name>')
def group_detail(group_id, group_name):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(
        user_email=user.email,
        group_id=group.id
    ).first_or_404()
    recipes = Recipe.query.filter_by(group_id=group.id).all()
    return render_template('group_page.html', group=group, recipes=recipes)
