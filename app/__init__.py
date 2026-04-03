from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from os import environ
import os

# force loading of environment variables
load_dotenv('.flaskenv')

DB_NAME = environ.get('SQLITE_DB')
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'csc33O'

DB_CONFIG_STR = 'sqlite:///' + os.path.join(basedir, DB_NAME)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONFIG_STR
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= True

print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Create database connection and associate it with the Flask application
db = SQLAlchemy(app)

# Add models
from app import routes, models