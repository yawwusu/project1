import os

from flask import Flask, session, render_template, request
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


@app.route("/home", methods=["POST"])
def home():
    """Homepage"""

    # Get form information.
    name = request.form.get("name")
    password = request.form.get("password")

    # Check if user exists.
    if db.execute("SELECT * FROM users WHERE name = :name AND password = :password", {"name": name, "password": password}).rowcount == 0:
        return render_template("error.html", message="No account with UserName and/or Password")

    books = db.execute("SELECT * FROM books").fetchall()
    return render_template("home.html", books=books)


@app.route("/result", methods=["POST"])
def books():
    """List all books which match search."""
    books = db.execute("SELECT * FROM books WHERE isbn = :search OR title = :search OR author = :search OR year = :search",
                        {"search": book_id}).fetchone()
    return render_template("result.html", books=books)


@app.route("/books/<int:book_id>")
def book(book_id):
    """List details about a single book."""

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", message="No such book.")

    # Get all reviews.
    review = db.execute("SELECT name FROM review WHERE book_id = :book_id",
                            {"book_id": book_id}).fetchall()
    return render_template("book.html", book=book, review=review)
