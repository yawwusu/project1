import os
import requests
from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

KEY = "UNvbUVCdWC5CR6kn5lUw"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/success", methods=["POST"])
def success():
    name = request.form.get("name")
    password = request.form.get("password")
    db.execute("INSERT INTO users (name, password) VALUES (:name, :password)",
            {"name": name, "password": password})
    db.commit()
    return render_template("success.html")


@app.route("/home", methods=["GET", "POST"])
def home():
    """Homepage"""

    # Get form information.
    name = request.form.get("name")
    password = request.form.get("password")

    # Check if user exists.
    user_id = db.execute("SELECT id FROM users WHERE name = :name AND password = :password",
                    {"name": name, "password": password}).fetchone()
    if user_id is None:
        return render_template("error.html", message="No account with UserName and/or Password")

    session["user_id"] = user_id[0]
    # books = db.execute("SELECT * FROM books").fetchall()
    return render_template("home.html")


@app.route("/result", methods=["POST"])
def result():
    """List all books which match search."""

    search = request.form.get("search")
    books = db.execute("SELECT * FROM books WHERE author = :search OR title = :search OR isbn = :search OR year = :search",
                        {"search": search}).fetchall()
    return render_template("result.html", books=books)


@app.route("/books/<int:book_id>")
def book(book_id):
    """List details about a single book."""

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="No such book.")

    # Get user
    # user_id = session["user_id"]
    # print(f"{user_id}")
    # names = db.execute("SELECT name FROM users").fetchall()
    # print(f"{names}")

    # Get all reviews.
    review = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": book.isbn})
    res_json = res.json()
    average = res_json["books"][0]["average_rating"]
    count = res_json["books"][0]["work_ratings_count"]
    return render_template("book.html", book=book, review=review, average=average, count=count)


@app.route("/books/<int:book_id>/review", methods= ["POST"])
def review(book_id):
    rate = request.form.get("rate")
    comment = request.form.get("comment")
    user_id = session["user_id"]
    db.execute("INSERT INTO reviews (rate,comment,book_id, user_id) VALUES (:rate, :comment, :book_id, :user_id)",
                    {"rate": rate, "comment": comment, "book_id": book_id, "user_id": user_id})
    db.commit()
    return render_template("review.html", book=book_id)

@app.route("/api/<isbn>")
def api(isbn):
    "Return api format"
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": isbn})
    res_json = res.json()
    average = res_json["books"][0]["average_rating"]
    count = res_json["books"][0]["work_ratings_count"]
    return jsonify({
    "title": book.title,
    "author": book.author,
    "year": book.year,
    "isbn": book.isbn,
    "review_count": count,
    "average_score": average})
