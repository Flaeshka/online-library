from flask import Flask, render_template, request, redirect, flash, session, send_file
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "my-secret-key"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db_connection():

    print("DATABASE:", os.path.abspath("database/library.db"))

    conn = sqlite3.connect("database/library.db")
    conn.row_factory = sqlite3.Row
    return conn



@app.route("/")
def home():
    conn = get_db_connection()

    users = conn.execute("SELECT * FROM users").fetchall()

    conn.close()

    return render_template("index.html", users=users)


@app.route("/my_library")
def my_book():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    books = conn.execute("""
        SELECT *
        FROM books
        WHERE author_id = ?
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "my_library.html",
        books=books
    )

    return render_template("my_library.html")


@app.route("/add_book", methods = ["GET", "POST"])
def add_book():

    if session.get("role") != "author":
        return "only author can add books"

    conn = get_db_connection()
    
    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        # Отримуємо всі вибрані жанри
        genre_ids = request.form.getlist("genres")

        book_file = request.files["book_file"]

        if book_file.filename == "":
            return "No file selected"

        if not book_file.filename.lower().endswith((".pdf", ".fb2")):
            conn.close()
            return "Only PDF and FB2 files are allowed"

        if not genre_ids:
            conn.close()
            return "Please select at least one genre"

        filename = secure_filename(book_file.filename)

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        book_file.save(file_path)
        # Створюємо книгу
        cursor = conn.execute("""
            INSERT INTO books
            (title, description, author_id, genre_id, file_path, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            session["user_id"],
            genre_ids[0],
            file_path,
            "pending"
        ))

        book_id = cursor.lastrowid

        # Додаємо жанри книги
        for genre_id in genre_ids:

            conn.execute("""
                INSERT INTO book_genres
                (book_id, genre_id)
                VALUES (?, ?)
            """, (
                book_id,
                genre_id
            ))

        conn.commit()
        conn.close()

        print("BOOK ADDED:", title)

        return "book added successfully"

    # Отримуємо жанри з БД
    genres = conn.execute("""
        SELECT *
        FROM genres
        ORDER BY name
    """).fetchall()

    conn.close()

    return render_template(
        "add_book.html",
        genres=genres
    )



@app.route("/register", methods=["GET", "POST"])
def register():
    #return render_template("register.html")
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        if role not in ["reader", "author"]:
            return "Invalid role"

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO users(username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (username, email, password, role))

        conn.commit()
        conn.close()
        session["username"] = username
        flash("Registration successful!")
        return redirect("/")
    return render_template("register.html")








@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()
        

        if user is not None and user["password_hash"] == password:
            session["username"] = user["username"]
            session["user_id"] = user["id"]
            session["role"] = user["role"]


            if user["role"] == "librarian":
                return redirect("/librarian")
            
            return redirect ("/")

        return "Wrong email or password!"

    return render_template("login.html")


@app.route("/librarian")
def librarian():

    if session.get("role") != "librarian":
        return "Access denied"

    return render_template("librarian.html")

@app.route("/librarian/pending")
def librarian_pending():

    if session.get("role") != "librarian":
        return "Access denied"

    conn = get_db_connection()

    books = conn.execute("""
        SELECT books.*, users.username AS author_name
        FROM books
        JOIN users ON books.author_id = users.id
        WHERE books.status = 'pending'
        ORDER BY books.created_at ASC
    """).fetchall()

    conn.close()

    return render_template(
        "librarian_pending.html",
        books=books
    )

@app.route("/librarian/book/<int:book_id>")
def librarian_book(book_id):

    if session.get("role") != "librarian":
        return "Access denied"

    conn = get_db_connection()

    book = conn.execute("""
        SELECT books.*, users.username AS author_name
        FROM books
        JOIN users ON books.author_id = users.id
        WHERE books.id = ?
    """, (book_id,)).fetchone()

    conn.close()

    if book is None:
        return "Book not found"

    return render_template(
        "librarian_book.html",
        book=book
    )

@app.route("/librarian/book/file/<int:book_id>")
def librarian_book_file(book_id):

    if session.get("role") != "librarian":
        return "Access denied"

    conn = get_db_connection()

    book = conn.execute("""
        SELECT file_path
        FROM books
        WHERE id = ?
    """, (book_id,)).fetchone()

    conn.close()

    if book is None:
        return "Book not found"

    file_path = book["file_path"]

    if not file_path or not os.path.exists(file_path):
        return "File not found"

    return send_file(file_path)

@app.route("/logout")
def logout():

    session.clear()
    flash("You have been logged out. Please register or log in to continue.")

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)