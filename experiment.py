import os, sys
import time
from functools import reduce
from flask import Flask, redirect, url_for, g, session, request
from flask_sqlalchemy import  SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:She68105028@localhost:3306/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db.create_all()

START = 0
SCANNED = 1
END = 2

saved_directory = os.path.dirname(os.path.abspath(__file__)) + '/static/'
print (saved_directory)
