from flask import Flask, render_template, request, redirect, flash, session
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

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        genre_name = request.form["genre"]

        book_file = request.files["book_file"]

        if book_file.filename == "":
            return "No file selected"

        if not book_file.filename.lower().endswith(".pdf"):
            return "Only PDF files  are allowed"

        filename = secure_filename(book_file.filename)

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        book_file.save(file_path)
        conn = get_db_connection()

        genre = conn.execute(
            "SELECT id FROM genres WHERE name = ?",
            (genre_name,)
        ).fetchone()

        # peding

        if genre is None:
            conn.execute(
                "INSERT INTO genres (name) VALUES (?)",
                (genre_name,)
            )

            conn.commit()

            genre = conn.execute(
                "SELECT id FROM genres WHERE name = ?",
                (genre_name,)
            ).fetchone()

        conn.execute("""
            INSERT INTO books
            (title, description, author_id, genre_id, file_path, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            session["user_id"],
            genre["id"],
            file_path,
            "pending"
        ))

        conn.commit()
        conn.close()

        print("BOOK ADDED:", title)
        return "book added successfully"
    return render_template("add_book.html")



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


            return redirect ("/")

        return "Wrong email or password!"

    return render_template("login.html")






@app.route("/logout")
def logout():

    session.clear()
    flash("You have been logged out. Please register or log in to continue.")

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)