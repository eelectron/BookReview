import os, requests

from flask import Flask, session, render_template, url_for, request, redirect, jsonify
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
# postgres://xqlpqzxylltuvf:6f4e2969fc6fa5aa129df741c341bf2bbd4a9f8d1fb6f0a0d05e8a8283e12dd9@ec2-184-73-153-64.compute-1.amazonaws.com:5432/df45h8i6h1g4nc
# postgres://prashantsingh:j@localhost:5432/postgres
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Goodreads api key
KEY = "k6fepBYZ2ZoNgVz6kfLg"

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/reg", methods=["POST", "GET"])
def reg():
	method = request.method
	if method == "POST":
		# register user if not already exist
		username = request.form.get("username")
		password = request.form.get("password")
		row = db.execute("SELECT * FROM users WHERE username = :username", {"username":username})
		if row.rowcount == 1:
			message = "user already exist"
			return render_template("error.html", message=message)
		else:
			db.execute("INSERT INTO users(username, password) VALUES(:username, :password)", {"username":username, "password":password})
			db.commit()
			# redirect to login
			return render_template("login.html")
	else:
		return render_template("registration.html")


@app.route("/login", methods=["GET", "POST"])
def login():
	method = request.method
	if method == "POST":
		username = request.form.get("username")
		password = request.form.get("password")
		
		# search books
		userRow = db.execute("SELECT * FROM users WHERE username = :username", {"username": username})
		if userRow.rowcount == 0:
			message = "user does not exist "
			return render_template("error.html", message=message)

		pwRow = db.execute("SELECT * FROM users WHERE password = :password", {"password": password})
		if pwRow.rowcount == 0:
			message = "Please enter correct password"
			return render_template("error.html", message=message)

		session["username"] = username
		return redirect(url_for("search"))
	else:
		return render_template("login.html")


@app.route("/search", methods=["GET", "POST"])
def search():
	method = request.method
	if method == "POST":
		query = request.form.get("query")
		query = "%" + query + "%"
		# get all books matching with query
		books = db.execute("SELECT * FROM books WHERE title LIKE :query OR isbn LIKE :query OR author LIKE :query OR year LIKE :query", {"query":query}).fetchall()
		return render_template("search.html", books=books)
	else:
		return render_template("search.html")

'''
Show the details of selected book .
'''
@app.route("/book/<isbn>")
def book(isbn):
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
	if book is None:
		return render_template("error.html", message="No such book")
	res 		= requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": isbn})
	resJson 	= res.json()
	bookReview 	= resJson["books"][0]

	#Show other users comment
	usersComment = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn":isbn}).fetchall()
	return render_template("book.html", book=book, bookReview = bookReview, usersComment=usersComment)

'''
Save review of the book for current user.
'''
@app.route("/saveReview/<isbn>", methods=["GET", "POST"])
def saveReview(isbn):
	method = request.method
	if method == "POST":
		username 	= session["username"]
		rating 		= request.form.get("rating")
		comment 	= request.form.get("comment")

		# if comment already exist then update it
		row = db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn", {"username":username, "isbn":isbn})
		if row.rowcount >= 1:
			db.execute("DELETE FROM reviews WHERE username = :username AND isbn = :isbn", {"username":username, "isbn":isbn, "rating":rating, "comment":comment})
		db.execute("INSERT INTO reviews(username, isbn, rating, comment) VALUES(:username, :isbn, :rating, :comment)", {"username":username, "isbn":isbn, "rating":rating, "comment":comment})
		db.commit()
		# message = "Your comment is saved successfully !"
		return redirect(url_for("book", isbn = isbn))
	else:
		message = "Please save comment properly."
		return render_template("error.html", message=message)


@app.route("/logout")
def logout():
	session.pop("username", None)
	return redirect(url_for("index"))

'''
Return results for books query .
This implements autosearch feature .
'''
@app.route("/books")
def books():
	query = request.args.get("query")
	query = "%" + query + "%"
	# get all books matching with query
	books = db.execute("SELECT * FROM books WHERE title ILIKE :query OR isbn ILIKE :query OR author ILIKE :query OR year ILIKE :query", {"query":query}).fetchall()
	return render_template("books.html", books=books)