from app import db

# Define the DB schema
class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(64), unique=True, nullable=False)
    population = db.Column(db.Integer, unique=False, nullable=False)

class Recipe(db.Model):
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(64), db.ForeignKey('user.email'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False, )
    title = db.Column(db.String(64), nullable=False)
    allergens = db.Column(db.array, nullable=True)
    prep_time = db.Column(db.Integer, nullable = False)
    cook_time = db.Column(db.Integer, nullable=False)
    body = db.Column(db.TEXT, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    num_serves = db.Column(db.Integer, nullable = False)
    privacy_setting = db.Column(db.String(64), nullable=False)
    is_validated = db.Column(db.Boolean, nullable=True)
    date_posted = db.Column(db.datetime, nullable=False)
    forked_from_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=True)

class User(db.Model):
    __tablename__ = 'user'
    email = db.Column(db.String(64), primary_key=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable = False)
    date_joined = db.Column(db.datetime, nullable=False)
    isPending = db.Column(db.Boolean, nullable=False)
