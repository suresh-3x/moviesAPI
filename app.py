from flask import Flask, jsonify, render_template
from flask_restful import Resource, Api, reqparse, abort, fields, marshal_with, request
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import pbkdf2_sha256 as sha256
import os
import datetime as dt
import pandas as pd
from flask_jwt_extended import (JWTManager, create_access_token)
import requests

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'somesfasfsaf-asfsafsfaecret-strafsasfing'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'datab.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
jwt = JWTManager(app)

class UserModel(db.Model):
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)
    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    roles = db.Column(db.Text)

class MoviesModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    movie_type = db.Column(db.String(100))
    genre = db.Column(db.Text)
    language = db.Column(db.String(20))
    runtime = db.Column(db.Integer)



movieResourceFields = {
    'name': fields.String,
    'movie_type': fields.String,
    'genre': fields.String,
    'language': fields.String,
    'runtime': fields.Integer
}

userResourceFields = {
    'username': fields.String,
    'roles': fields.String
}

userPostargs = reqparse.RequestParser()
userPostargs.add_argument("username", type=str, help="username for the user is required", required=True)
userPostargs.add_argument("password", type=str, help="password for the user is required", required=True)
userPostargs.add_argument("roles", type=str)

class Movies(Resource):
    @marshal_with(movieResourceFields)
    def get(self):
        if len(request.args) == 0:
            allMovies = MoviesModel.query.all()
            return allMovies
        elif request.args.get('type') and request.args.get('sort'):
            movies = MoviesModel.query.filter_by(movie_type=request.args.get('type')).order_by(request.args.get('sort')).all()
            return movies
        elif len(request.args) == 1 and request.args.get('type'):
            movies = MoviesModel.query.filter_by(movie_type=request.args.get('type')).all()
            return movies
        elif len(request.args) == 1 and request.args.get('sortBy'):
            movies = MoviesModel.query.order_by(request.args.get('sortBy')).all()
            return movies
        elif len(request.args) == 1 and request.args.get('searchByGenre'):
            movies =  MoviesModel.query.filter(MoviesModel.genre.like(f"%{request.args.get('searchByGenre')}%")).all()
            return movies
        else:
            abort(404, message="Please check the url")



class UserRegister(Resource):
    @marshal_with(userResourceFields)
    def post(self):
        args = userPostargs.parse_args()
        user = UserModel.query.filter_by(username=args['username']).first()
        if user:
            abort(409, message="Username is already taken.")
        user = UserModel(username=args['username'], password=UserModel.generate_hash(args['password']), roles=args['roles'])
        db.session.add(user)
        db.session.commit()
        return user, 201

class UserLogin(Resource):
    def post(self):
        args = userPostargs.parse_args()
        user = UserModel.query.filter_by(username=args['username']).first()
        if not user:
            abort(404, message="User not found")
        
        if UserModel.verify_hash(args['password'], user.password):
            access_token = create_access_token(identity=args['username'])
            return jsonify(access_token=access_token)
        else:
            return {'message': 'wrong credentials'}

api.add_resource(Movies, '/api/movies')
api.add_resource(UserRegister, '/api/authenticate/register')
api.add_resource(UserLogin, '/api/authenticate/login')



@app.route('/')
def home():
    data = requests.get('http://127.0.0.1:5000/api/movies').json()
    return render_template('index.html', data=data)



if __name__ == '__main__':
    app.run(debug=True)