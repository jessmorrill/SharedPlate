from app import db

# Define the DB schema
class Recipe(db.Model):
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(64), db.ForeignKey('user.email'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    prep_time = db.Column(db.Integer, nullable = False)
    cook_time = db.Column(db.Integer, nullable=False)
    body = db.Column(db.TEXT, nullable=False)
    num_serves = db.Column(db.Integer, nullable = False)
    privacy_setting = db.Column(db.String(64), nullable=False)
    is_validated = db.Column(db.Boolean, nullable=True)
    date_posted = db.Column(db.TEXT, nullable=False)
    forked_from_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=True)
    ingredients = db.relationship('Ingredient', backref='recipe', lazy=True)
    author = db.relationship('User', foreign_keys=[user_email], backref='recipes')
    
class User(db.Model):
    __tablename__ = 'user'
    email = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable = False)
    date_joined = db.Column(db.TEXT, nullable=False)
    isPending = db.Column(db.Boolean, nullable=False)
    memberships = db.relationship('Group_Membership', backref='user', lazy=True)
    
class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(64), nullable=False)
    privacy_setting = db.Column(db.String(64), nullable=False)
    memberships = db.relationship('Group_Membership', backref='group', lazy=True)
    recipes = db.relationship('Recipe', backref='group', lazy=True)
    
class Group_Membership(db.Model):
    __tablename__ = 'group_membership'
    user_email = db.Column(db.String(64), db.ForeignKey('user.email'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), primary_key=True)
    role = db.Column(db.String(64), nullable=False)
    notify_if_review = db.Column(db.Boolean, nullable=False)
    notify_if_fork = db.Column(db.Boolean, nullable=False)
    notify_if_change = db.Column(db.Boolean, nullable=False)

class JoinRequest(db.Model):
    __tablename__ = 'join_request'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(64), db.ForeignKey('user.email'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    status = db.Column(db.String(64), nullable=False, default='pending')  # pending, accepted, denied
    date_requested = db.Column(db.TEXT, nullable=False)
    user = db.relationship('User', foreign_keys=[user_email], backref='join_requests')
    group = db.relationship('Group', foreign_keys=[group_id], backref='join_requests')

class Invite(db.Model):
    __tablename__ = 'invite'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    inviter_email = db.Column(db.String(64), db.ForeignKey('user.email'), nullable=False)
    invitee_email = db.Column(db.String(64), db.ForeignKey('user.email'), nullable=False)
    status = db.Column(db.String(64), nullable=False, default='pending')  # pending, accepted, declined
    date_invited = db.Column(db.TEXT, nullable=False)
    group = db.relationship('Group', foreign_keys=[group_id], backref='invites')
    inviter = db.relationship('User', foreign_keys=[inviter_email], backref='sent_invites')
    invitee = db.relationship('User', foreign_keys=[invitee_email], backref='received_invites')

class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
    name = db.Column(db.String(64), primary_key=True)
    num = db.Column(db.Integer, nullable=False)
    units = db.Column(db.String(64), nullable=False)