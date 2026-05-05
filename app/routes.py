from app import app, db, mail
from sqlalchemy import func
from flask import session, render_template, redirect, url_for, request, flash
from flask_mail import Message
from app.forms import CreateRecipe, SearchRecipe, CreateGroup, SearchGroup
from app.models import Recipe, Ingredient, Group, User, Group_Membership, JoinRequest, Invite, LikedRecipe, Review
from datetime import datetime
import random
import pdb

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


def clear_pending_registration():
    pending_email = session.pop('pending_verify_email', None)
    session.pop('verify_code', None)
    if pending_email:
        pending_user = User.query.filter_by(email=pending_email, isPending=True).first()
        if pending_user:
            db.session.delete(pending_user)
            db.session.commit()


@app.before_request
def require_login_or_register():
    allowed_paths = {'/login', '/register', '/forgot-password', '/reset-password', '/verify'}
    if request.endpoint == 'static':
        return

    if session.get('pending_verify_email') and request.path != '/verify':
        clear_pending_registration()

    if session.get('user'):
        return

    user_email = request.args.get('user')
    if user_email:
        existing = User.query.filter_by(email=user_email).first()
        if existing and not existing.isPending:
            session['user'] = existing.email
            return

    if request.path not in allowed_paths:
        return redirect(url_for('login'))



@app.route('/', methods=['GET'])
def home():
    greetings = ("What's on your plate for today?", "Hungry for something new?", "Discover your next favorite recipe!", 
                 "Welcome back!", "What are you going to make today?", "Happy Cooking!", "Cheat on your diet... we won't tell!", 
                 "Just like grandma used to make!", "How can we inspire your next meal?")
    greeting = random.choice(greetings)
    form = SearchRecipe(request.args)
    form2 = SearchGroup(request.args)
    sort_by = request.args.get('sort_by', 'date_desc')
    recipes_query = Recipe.query.filter_by(privacy_setting='public')
    groups_query = Group.query.filter_by(privacy_setting='public')
    if form.searchA.data and form.searchA.data.strip():
        recipes_query = recipes_query.filter(
            Recipe.title.ilike(f"%{form.searchA.data}%")
        )
    if sort_by == 'likes':
        recipes_query = recipes_query.outerjoin(LikedRecipe).group_by(Recipe.id).order_by(func.count(LikedRecipe.recipe_id).desc())
    elif sort_by == 'rating':
        recipes_query = recipes_query.outerjoin(Review).group_by(Recipe.id).order_by(func.coalesce(func.avg(Review.rating), 0).desc())
    elif sort_by == 'date_oldest':
        recipes_query = recipes_query.order_by(Recipe.date_posted.asc())
    else:
        recipes_query = recipes_query.order_by(Recipe.date_posted.desc())
    if form2.searchB.data and form2.searchB.data.strip():
        groups_query = groups_query.filter(
            Group.group_name.ilike(f"%{form2.searchB.data}%")
        )
    recipes = recipes_query.all()
    groups = groups_query.all()
    return render_template('index.html', recipes=recipes, groups=groups, form=form, form2=form2, greeting=greeting, sort_by=sort_by)


@app.route('/recipe/<int:recipe_id>', methods=['GET'])
def recipe_detail(recipe_id):
    user = get_current_user()
    recipe = Recipe.query.get_or_404(recipe_id)
    ingredients = Ingredient.query.filter_by(recipe_id=recipe_id).all()
    liked = False
    user_review = None
    if user:
        liked = LikedRecipe.query.filter_by(user_email=user.email, recipe_id=recipe_id).first() is not None
        user_review = Review.query.filter_by(user_email=user.email, recipe_id=recipe_id).first()
    num_likes = db.session.query(func.count(LikedRecipe.recipe_id)).filter(LikedRecipe.recipe_id == recipe_id).scalar()
    if user_review:
        other_reviews = Review.query.filter(Review.recipe_id == recipe_id, Review.user_email != user.email).order_by(Review.date_posted.desc()).all()
    else:
        other_reviews = Review.query.filter_by(recipe_id=recipe_id).order_by(Review.date_posted.desc()).all()
    like_text = "like" if num_likes == 1 else "likes"
    return render_template(
        'recipe_detail.html',
        recipe=recipe,
        ingredients=ingredients,
        liked=liked,
        num_likes=num_likes,
        like_text=like_text,
        user_review=user_review,
        other_reviews=other_reviews
    )


@app.route('/recipe/<int:recipe_id>/toggle_like', methods=['POST'])
def toggle_like(recipe_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    recipe = Recipe.query.get_or_404(recipe_id)
    existing_like = LikedRecipe.query.filter_by(user_email=user.email, recipe_id=recipe_id).first()
    if existing_like:
        db.session.delete(existing_like)
        flash(f'Recipe "{recipe.title}" removed from liked recipes.', 'success')
    else:
        like = LikedRecipe(user_email=user.email, recipe_id=recipe_id)
        db.session.add(like)
        flash(f'Recipe "{recipe.title}" added to liked recipes.', 'success')
    db.session.commit()
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))


@app.route('/recipe/<int:recipe_id>/review', methods=['POST'])
def submit_review(recipe_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    recipe = Recipe.query.get_or_404(recipe_id)
    existing_review = Review.query.filter_by(user_email=user.email, recipe_id=recipe_id).first()
    if existing_review:
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    if user.email == recipe.user_email:
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    title = request.form.get('title', '').strip()
    rating = request.form.get('rating')
    comment = request.form.get('comment', '').strip()
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        rating = None
    if rating not in [1, 2, 3, 4, 5] or not comment:
        flash('Please provide a rating and a comment.', 'warning')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    review = Review(
        user_email=user.email,
        recipe_id=recipe_id,
        title=title,
        rating=rating,
        comment=comment,
        date_posted=datetime.now()
    )
    db.session.add(review)
    db.session.commit()
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))



@app.route('/create-recipe', methods=['GET', 'POST'])
def add_recipe():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    group_id = request.args.get('group_id') if request.method == 'GET' else request.form.get('group_id')
    if not group_id:
        return redirect(url_for('home'))

    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    if not membership:
        return redirect(url_for('group_detail', group_id=group.id, group_name=group.group_name))

    form = CreateRecipe()
    if request.method == 'GET':
        form.privacy.data = 'private'

    if form.validate_on_submit():
        title = form.title.data
        prep_time = form.prep_time.data
        cook_time = form.cook_time.data
        body = form.body.data
        num_serves = form.num_serves.data
        privacy = form.privacy.data

        c = Recipe(
            user_email=session.get('user'),
            group_id=group.id,
            title=title,
            prep_time=prep_time,
            cook_time=cook_time,
            body=body,
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
        flash(f'Recipe "{title}" created!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=c.id))  # FIX: redirect to recipe page

    if request.method == 'POST':
        flash('Failed to create recipe. Please check the form for errors.', 'danger')
    return render_template('add.html', form=form, group=group)


@app.route('/create-group', methods=['GET', 'POST'])
def add_group():
    form = CreateGroup()
    if form.validate_on_submit():
        group_name = form.group_name.data
        privacy = form.privacy.data
        c = Group(group_name=group_name, privacy_setting=privacy)
        db.session.add(c)
        db.session.flush()
        membership = Group_Membership(
            user_email=session.get('user'),
            group_id=c.id,
            role='creator',
            notify_if_review=True,
            notify_if_like=True
        )
        db.session.add(membership)
        db.session.commit()
        flash(f'Group "{group_name}" created!', 'success')
        return redirect(url_for('group_detail', group_id=c.id, group_name=c.group_name))  
    return render_template('create_group.html', form=form)  


@app.route('/join-group', methods=['GET', 'POST'])
def join_group():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    form = SearchGroup(request.args if request.method == 'GET' else request.form)
    query = form.searchB.data.strip() if form.searchB.data else ''

    membership_ids = [m.group_id for m in Group_Membership.query.filter_by(user_email=user.email).all()]

    group_query = Group.query.filter(~Group.id.in_(membership_ids))
    if query:
        group_query = group_query.filter(Group.group_name.ilike(f"%{query}%"))
    groups = group_query.all()

    return render_template('join_group.html', form=form, groups=groups, membership_ids=membership_ids)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        existing_email = User.query.filter_by(email=email).first()
        existing_username = User.query.filter_by(username=username).first()
        if existing_email:
            return render_template('register.html', error='Email already registered')
        if existing_username:
            return render_template('register.html', error='Username already taken')
        if not existing_email and not existing_username:
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

            session['pending_verify_email'] = email
            session['verify_code'] = code

            msg = Message('Your verification code', recipients=[email])
            msg.body = f'Your SharedPlate verification code is: {code}'
            mail.send(msg)

            return redirect(url_for('verify'))

    return render_template('register.html', error=None)


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        entered = request.form.get('code')
        if entered == session.get('verify_code'):
            pending_email = session.get('pending_verify_email')
            user = User.query.filter_by(email=pending_email).first()
            if user:
                user.isPending = False
                db.session.commit()
                session.pop('verify_code', None)
                session.pop('pending_verify_email', None)
                session['user'] = user.email
                return redirect(url_for('home'))
        else:
            return render_template('verify.html', error='Incorrect code, try again.')
    return render_template('verify.html', error=None)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            code = str(random.randint(100000, 999999))
            session['reset_email'] = email
            session['reset_code'] = code
            msg = Message('Password Reset Code', recipients=[email])
            msg.body = f'Your SharedPlate password reset code is: {code}'
            mail.send(msg)
            return redirect(url_for('reset_password'))
        else:
            return render_template('forgot_password.html', error='Email not found.')
    return render_template('forgot_password.html', error=None)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        entered = request.form.get('code')
        password = request.form.get('password')
        if entered == session.get('reset_code'):
            user = User.query.filter_by(email=session.get('reset_email')).first()
            if user:
                user.password = password
                db.session.commit()
                session.pop('reset_code', None)
                session.pop('reset_email', None)
                return redirect(url_for('login'))
        else:
            return render_template('reset_password.html', error='Incorrect code, try again.')
    return render_template('reset_password.html', error=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('email')
        password = request.form.get('password')
        if '@' in login_input:
            user = User.query.filter_by(email=login_input, password=password).first()
        else:
            user = User.query.filter_by(username=login_input, password=password).first()
        if user and not user.isPending:
            session['user'] = user.email
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Username or password is incorrect')
    return render_template('login.html', error=None)


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
    creator_memberships = Group_Membership.query.filter_by(user_email=user.email, role='creator').all()
    creator_group_ids = [m.group_id for m in creator_memberships]
    pending_requests = JoinRequest.query.filter(JoinRequest.group_id.in_(creator_group_ids), JoinRequest.status == 'pending').all()
    pending_invites = Invite.query.filter_by(invitee_email=user.email, status='pending').all()
    liked_items = LikedRecipe.query.filter_by(user_email=user.email).all()
    liked_recipes = [item.recipe for item in liked_items]
    return render_template('dashboard.html', user=user, recipes=recipes, groups=groups, pending_requests=pending_requests, pending_invites=pending_invites, liked_recipes=liked_recipes)


@app.route('/group/<int:group_id>-<string:group_name>')
def group_detail(group_id, group_name):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    creator_membership = Group_Membership.query.filter_by(group_id=group.id, role='creator').first()
    creator_username = None
    if creator_membership:
        creator_username = creator_membership.user.username
    if not membership and group.privacy_setting == 'private':
        return render_template('group_page.html', group=group, membership=None, can_request=True, creator_username=creator_username)
    sort_by = request.args.get('sort_by', 'date_desc')
    recipes_query = Recipe.query.filter_by(group_id=group.id)
    if sort_by == 'likes':
        recipes_query = recipes_query.outerjoin(LikedRecipe).group_by(Recipe.id).order_by(func.count(LikedRecipe.recipe_id).desc())
    elif sort_by == 'rating':
        recipes_query = recipes_query.outerjoin(Review).group_by(Recipe.id).order_by(func.coalesce(func.avg(Review.rating), 0).desc())
    elif sort_by == 'date_oldest':
        recipes_query = recipes_query.order_by(Recipe.date_posted.asc())
    else:
        recipes_query = recipes_query.order_by(Recipe.date_posted.desc())
    recipes = recipes_query.all()
    return render_template('group_page.html', group=group, recipes=recipes, membership=membership, can_request=(not membership and group.privacy_setting == 'public'), creator_username=creator_username, sort_by=sort_by)


@app.route('/group/<int:group_id>/request_join', methods=['POST'])
def request_join(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    existing_membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    if existing_membership:
        flash('You are already a member of this group.', 'warning')
        return redirect(url_for('group_detail', group_id=group.id, group_name=group.group_name))

    if group.privacy_setting == 'public':
        membership = Group_Membership(
            user_email=user.email,
            group_id=group.id,
            role='member',
            notify_if_review=True,
            notify_if_like=True
        )
        db.session.add(membership)
        db.session.commit()
        flash(f'You have joined "{group.group_name}"!', 'success') 
        return redirect(url_for('group_detail', group_id=group.id, group_name=group.group_name))

    existing_request = JoinRequest.query.filter_by(user_email=user.email, group_id=group.id, status='pending').first()
    if existing_request:
        flash('You already have a pending request for this group.', 'warning')  
        return redirect(url_for('group_detail', group_id=group.id, group_name=group.group_name))

    request_obj = JoinRequest(
        user_email=user.email,
        group_id=group.id,
        date_requested=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(request_obj)
    db.session.commit()
    flash(f'Your request to join "{group.group_name}" has been sent.', 'info')
    creator_membership = Group_Membership.query.filter_by(group_id=group.id, role='creator').first()
    if creator_membership:
        creator = User.query.filter_by(email=creator_membership.user_email).first()
        if creator:
            msg = Message('Join Request for Your Group', recipients=[creator.email])
            msg.body = f'{user.username} has requested to join your group "{group.group_name}".\n\nTo manage this request, visit: {url_for("manage_requests", group_id=group.id, user=creator.email, _external=True)}'
            mail.send(msg)

    return redirect(url_for('group_detail', group_id=group.id, group_name=group.group_name))


@app.route('/group/<int:group_id>/manage_requests')
def manage_requests(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    if not membership or membership.role != 'creator':
        return redirect(url_for('home'))
    requests = JoinRequest.query.filter_by(group_id=group.id, status='pending').all()
    return render_template('manage_requests.html', group=group, requests=requests)


@app.route('/group/<int:group_id>/add_members', methods=['GET', 'POST'])
def add_members(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    if not membership or membership.role != 'creator':
        return redirect(url_for('home'))

    search_results = []
    search_query = ''
    if request.method == 'POST':
        search_query = request.form.get('username', '').strip()
    elif request.method == 'GET':
        search_query = request.args.get('search_query', '').strip()

    if search_query:
        users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
        for u in users:
            existing_membership = Group_Membership.query.filter_by(user_email=u.email, group_id=group.id).first()
            if existing_membership:
                continue
            pending_invite = Invite.query.filter_by(group_id=group.id, invitee_email=u.email, status='pending').first()
            status = 'pending' if pending_invite else 'available'
            search_results.append({'user': u, 'status': status})

        if not search_results:
            flash('No users found matching that username.', 'warning')

    return render_template('add_members.html', group=group, search_query=search_query, search_results=search_results)


@app.route('/group/<int:group_id>/invite/<invitee_email>', methods=['POST'])
def invite_user(group_id, invitee_email):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    if not membership or membership.role != 'creator':
        return redirect(url_for('home'))

    invitee = User.query.filter_by(email=invitee_email).first()
    if not invitee:
        flash('User not found.', 'danger')
        return redirect(url_for('add_members', group_id=group_id))

    existing_invite = Invite.query.filter_by(group_id=group.id, invitee_email=invitee_email, status='pending').first()
    if existing_invite:
        flash(f'{invitee.username} has already been invited.', 'warning')
        return redirect(url_for('add_members', group_id=group_id, search_query=request.form.get('search_query', '')))
    existing_membership = Group_Membership.query.filter_by(user_email=invitee_email, group_id=group.id).first()
    if existing_membership:
        flash(f'{invitee.username} is already a member.', 'warning') 
        return redirect(url_for('add_members', group_id=group_id, search_query=request.form.get('search_query', '')))

    invite = Invite(
        group_id=group.id,
        inviter_email=user.email,
        invitee_email=invitee_email,
        date_invited=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(invite)
    db.session.commit()

    msg = Message('Group Invitation', recipients=[invitee_email])
    msg.body = f'You have been invited to join the group "{group.group_name}" by {user.username}.\n\nTo accept or decline, visit: {url_for("manage_invite", invite_id=invite.id, user=invitee_email, _external=True)}'
    mail.send(msg)

    flash(f'Invite sent to {invitee.username}!', 'success') 
    return redirect(url_for('add_members', group_id=group_id, search_query=request.form.get('search_query', '')))  # FIX: preserve search


@app.route('/group/<int:group_id>/leave', methods=['POST'])
def leave_group(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group_id).first()
    if not membership:
        flash('You are not a member of that group.', 'warning')
        return redirect(url_for('home'))
    if membership.role == 'creator':
        flash('Group creators must delete the group instead of leaving it.', 'warning')
        group = Group.query.get_or_404(group_id)
        return redirect(url_for('group_detail', group_id=group.id, group_name=group.group_name))
    group_name = membership.group.group_name if membership.group else 'the group'
    db.session.delete(membership)
    db.session.commit()
    flash(f'You have left "{group_name}".', 'success')
    return redirect(url_for('home'))


@app.route('/group/<int:group_id>/delete', methods=['POST'])
def delete_group(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    if not membership or membership.role != 'creator':
        return redirect(url_for('home'))

    Invite.query.filter_by(group_id=group.id).delete()
    JoinRequest.query.filter_by(group_id=group.id).delete()
    for recipe in Recipe.query.filter_by(group_id=group.id).all():
        Ingredient.query.filter_by(recipe_id=recipe.id).delete()
        db.session.delete(recipe)
    Group_Membership.query.filter_by(group_id=group.id).delete()
    db.session.delete(group)
    db.session.commit()

    flash(f'Group "{group.group_name}" has been deleted.', 'success')
    return redirect(url_for('home'))


@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_email != user.email:
        return redirect(url_for('home'))
    group_name = recipe.group.group_name if recipe.group else ''
    group_id = recipe.group_id
    Ingredient.query.filter_by(recipe_id=recipe.id).delete()
    db.session.delete(recipe)
    db.session.commit()

    flash(f'Recipe "{recipe.title}" deleted.', 'success')
    if group_name:
        return redirect(url_for('group_detail', group_id=group_id, group_name=group_name))
    return redirect(url_for('home'))


@app.route('/invite/<int:invite_id>', methods=['GET'])
def manage_invite(invite_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    invite = Invite.query.get_or_404(invite_id)
    if invite.invitee_email != user.email or invite.status != 'pending':
        return redirect(url_for('home'))

    return render_template('manage_invite.html', invite=invite)


@app.route('/invite/<int:invite_id>/accept', methods=['POST'])
def accept_invite(invite_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    invite = Invite.query.get_or_404(invite_id)
    if invite.invitee_email != user.email or invite.status != 'pending':
        return redirect(url_for('home'))

    membership = Group_Membership(
        user_email=user.email,
        group_id=invite.group_id,
        role='member',
        notify_if_review=True,
        notify_if_like=True
    )
    db.session.add(membership)
    invite.status = 'accepted'
    db.session.commit()

    flash(f'You have joined "{invite.group.group_name}"!', 'success') 
    return redirect(url_for('group_detail', group_id=invite.group_id, group_name=invite.group.group_name))  # FIX: redirect to group


@app.route('/invite/<int:invite_id>/decline', methods=['POST'])
def decline_invite(invite_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    invite = Invite.query.get_or_404(invite_id)
    if invite.invitee_email != user.email or invite.status != 'pending':
        return redirect(url_for('home'))

    invite.status = 'declined'
    db.session.commit()

    flash('Invite declined.', 'info')  # FIX: success case
    return redirect(url_for('dashboard'))


@app.route('/group/<int:group_id>/accept_request/<int:request_id>', methods=['POST'])
def accept_request(group_id, request_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    if not membership or membership.role != 'creator':
        return redirect(url_for('home'))
    request_obj = JoinRequest.query.get_or_404(request_id)
    if request_obj.group_id != group_id or request_obj.status != 'pending':
        return redirect(url_for('dashboard'))

    new_membership = Group_Membership(
        user_email=request_obj.user_email,
        group_id=group.id,
        role='member',
        notify_if_review=True,
        notify_if_like=True
    )
    db.session.add(new_membership)
    request_obj.status = 'accepted'
    db.session.commit()

    requester = User.query.filter_by(email=request_obj.user_email).first()
    if requester:
        msg = Message('Join Request Accepted', recipients=[requester.email])
        msg.body = f'Your request to join the group "{group.group_name}" has been accepted! You are now a member.'
        mail.send(msg)

    flash(f'{requester.username if requester else "User"} has been accepted into the group.', 'success')  # FIX: success case
    return redirect(url_for('manage_requests', group_id=group_id))  # FIX: stay on manage requests


@app.route('/group/<int:group_id>/deny_request/<int:request_id>', methods=['POST'])
def deny_request(group_id, request_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    group = Group.query.get_or_404(group_id)
    membership = Group_Membership.query.filter_by(user_email=user.email, group_id=group.id).first()
    if not membership or membership.role != 'creator':
        return redirect(url_for('home'))
    request_obj = JoinRequest.query.get_or_404(request_id)
    if request_obj.group_id != group_id or request_obj.status != 'pending':
        return redirect(url_for('dashboard'))

    request_obj.status = 'denied'
    db.session.commit()

    flash('Request denied.', 'info') 
    return redirect(url_for('manage_requests', group_id=group_id)) 

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
