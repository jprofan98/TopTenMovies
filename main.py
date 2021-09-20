from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests

"""
TODO:
    1. Add error handling when selecting movie (crashes if user attempts to add same movie again)
    2. Add + style back buttons to add.html and edit.html
    3. Prevent list from returning more than 10 movies
    4. Add secondary page that renders all movies in database in "bookshelf" format 
    5. Design + implement additional features for secondary page
"""

TMDB_API_KEY = 'e963171a66dd5ae4c2fdd9792694c013'
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_database.db'
Bootstrap(app)
db = SQLAlchemy(app)


# Create form to search for movies by title
class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

# Create form used to edit rating and comments on movie
class EditForm(FlaskForm):
    rating = FloatField('Your Rating Out of 10', validators=[DataRequired(),NumberRange(0,10)])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')

# Use SQLAlchemy to create table of movies with movie data
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float(), nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)


db.create_all()

# Helper function, makes API call to TMDB and returns a list of all movies related to that title
def process_add_movie(title):
    response = requests.get(
        f"https://api.themoviedb.org/3/search/movie?api_key=e963171a66dd5ae4c2fdd9792694c013&language=en-US&query={title}&include_adult=false")
    data = response.json()
    movie_list = data['results']

    return movie_list

# Homepage, renders the list of movies in order based on user rating
@app.route("/")
def home():
    movie_list = Movie.query.order_by(Movie.rating).all()

    for i in range(len(movie_list)):
        movie_list[i].ranking = len(movie_list) - i
    db.session.commit()
    return render_template("index.html", movies=movie_list)

# Renders the page for searching for movie by title, on form submission redirects to page to select movie
@app.route('/add', methods=['GET', 'POST'])
def add_movie():
    movie_add = AddForm()
    if request.method == 'POST':
        movie_title = request.form.get('title')
        return redirect(url_for('select_movie', title=movie_title))
    return render_template('add.html', form=movie_add)

# Renders the list of movies related to the given title
@app.route('/select')
def select_movie():
    movie_title = request.args.get('title')
    movie_list = process_add_movie(movie_title)
    return render_template('select.html', movies=movie_list)

# After user selects a movie from the above page, calls TMDB API for the chosen movie and adds relevant data to the database entry. Redirects user to edit page
@app.route('/find')
def find_movie():
    movie_id = request.args.get("id")
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US")
    data = response.json()
    movie_to_add = Movie(
        title=data['original_title'],
        description=data['overview'],
        year=int(data['release_date'].split('-')[0]),
        img_url="https://image.tmdb.org/t/p/w500" + data['poster_path']
    )

    db.session.add(movie_to_add)
    db.session.commit()

    return redirect(url_for('edit_movie', id=movie_to_add.id))

# Loads form that allows user to adjust the rating and comments for a particular movie, or set initial rating and comments if movie has just been added
@app.route('/edit', methods=['GET', 'POST'])
def edit_movie():
    movie_edit = EditForm()
    if request.method == "POST":
        movie_id = request.args.get('id')
        movie_to_update = Movie.query.get(movie_id)
        new_rating = request.form.get('rating')
        new_review = request.form.get('review')
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=movie_edit)

# Deletes a particular movie from the database
@app.route('/delete')
def delete_movie():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
