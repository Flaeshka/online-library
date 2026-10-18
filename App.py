from flask import Flask, render_template, request, redirect, flash, session, send_file, jsonify
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

    books = conn.execute("""
        SELECT books.*, users.username AS author_name
        FROM books
        JOIN users ON books.author_id = users.id
        WHERE books.status = 'approved'
        ORDER BY books.approved_at DESC
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        books=books
    )


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

@app.route("/author/profile", methods=["GET", "POST"])
def author_profile():

    if session.get("role") != "author":
        return "Access denied"

    conn = get_db_connection()

    if request.method == "POST":

        author_name = request.form["author_name"]

        conn.execute("""
            UPDATE users
            SET author_name = ?
            WHERE id = ?
        """, (
            author_name,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/my_library")

    user = conn.execute("""
        SELECT author_name
        FROM users
        WHERE id = ?
    """, (session["user_id"],)).fetchone()

    conn.close()

    return render_template(
        "author_profile.html",
        user=user
    )

@app.route("/add_book", methods = ["GET", "POST"])
def add_book():

    if session.get("role") != "author":
        return "only author can add books"

    conn = get_db_connection()
    
    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        publication_date = request.form.get("publication_date")

        print("PUBLICATION DATE:", publication_date)
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

        print("FILE PATH:", file_path)
        print("FILE EXISTS:", os.path.exists(file_path))
        
        # Створюємо книгу
        cursor = conn.execute("""
            INSERT INTO books
            (title, description, author_id, genre_id, file_path, status, publication_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            session["user_id"],
            genre_ids[0],
            file_path,
            "pending",
            publication_date
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

        flash("Book added successfully!")
        return redirect("/add_book")

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

@app.route("/book/<int:book_id>")
def book(book_id):
    conn = get_db_connection()

    book = conn.execute("""
        SELECT books.*, users.username AS author_name
        FROM books
        JOIN users ON books.author_id = users.id
        WHERE books.id = ? AND books.status = 'approved'
    """, (book_id,)).fetchone()

    conn.close()

    if book is None:
        return "Book not found"

    return render_template("book.html", book=book)

@app.route("/book/file/<int:book_id>")
def book_file(book_id):

    conn = get_db_connection()

    book = conn.execute("""
        SELECT file_path, title, status
        FROM books
        WHERE id = ?
    """, (book_id,)).fetchone()

    conn.close()

    if book is None:
        return "Book not found"

    print("BOOK:", book["title"])
    print("STATUS:", book["status"])
    print("FILE PATH:", book["file_path"])
    print("FILE EXISTS:", os.path.exists(book["file_path"]) if book["file_path"] else False)

    if book["status"] != "approved":
        return "Book is not approved"

    file_path = book["file_path"]

    if not file_path:
        return "File path is empty"

    if not os.path.exists(file_path):
        return "File not found"

    return send_file(
        file_path,
        as_attachment=False
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

    conn = get_db_connection()

    # Всі схвалені книги
    books = conn.execute("""
        SELECT books.*, users.username AS author_name
        FROM books
        JOIN users ON books.author_id = users.id
        WHERE books.status = 'approved'
        ORDER BY books.approved_at DESC
    """).fetchall()

    # Кількість книг, які очікують перевірки
    pending_count = conn.execute("""
        SELECT COUNT(*)
        FROM books
        WHERE status = 'pending'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "librarian.html",
        books=books,
        pending_count=pending_count
    )



@app.route("/librarian/pending")
def librarian_pending():

    if session.get("role") != "librarian":
        return "Access denied"

    search_query = request.args.get("q", "").strip()

    # Дозволені поля пошуку
    available_fields = {
        "title": "books.title",
        "author": """
            COALESCE(
                NULLIF(users.author_name, ''),
                users.username
            )
        """,
        "email": "users.email"
    }

    # Отримуємо вибрані поля з форми
    selected_fields = request.args.getlist("fields")

    # Відкидаємо невідомі значення
    selected_fields = [
        field for field in selected_fields
        if field in available_fields
    ]

    # Якщо нічого не вибрано, шукаємо за всіма полями
    if not selected_fields:
        selected_fields = list(available_fields.keys())

    conn = get_db_connection()

    sql = """
        SELECT
            books.*,
            COALESCE(
                NULLIF(users.author_name, ''),
                users.username
            ) AS author_name,
            users.email AS author_email,
            GROUP_CONCAT(DISTINCT genres.name) AS genres
        FROM books
        JOIN users ON books.author_id = users.id
        LEFT JOIN book_genres ON books.id = book_genres.book_id
        LEFT JOIN genres ON book_genres.genre_id = genres.id
        WHERE books.status = 'pending'
    """

    params = []

    # Додаємо умови пошуку, якщо введено текст
    if search_query:
        conditions = []

        for field in selected_fields:
            conditions.append(
                f"{available_fields[field]} LIKE ?"
            )
            params.append(f"%{search_query}%")

        sql += " AND (" + " OR ".join(conditions) + ")"

    sql += """
        GROUP BY books.id
        ORDER BY books.created_at ASC
    """

    books = conn.execute(sql, params).fetchall()

    conn.close()

    return render_template(
        "librarian_pending.html",
        books=books,
        search_query=search_query,
        search_fields=selected_fields
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


@app.route("/librarian/book/<int:book_id>/approve", methods=["POST"])
def approve_book(book_id):

    if session.get("role") != "librarian":
        return "Access denied"

    conn = get_db_connection()

    conn.execute("""
        UPDATE books
        SET status = 'approved',
            approved_at = CURRENT_TIMESTAMP,
            rejected_at = NULL
        WHERE id = ?
    """, (book_id,))

    conn.commit()
    conn.close()

    return redirect("/librarian/pending")


@app.route("/librarian/book/<int:book_id>/reject", methods=["POST"])
def reject_book(book_id):

    if session.get("role") != "librarian":
        return "Access denied"

    conn = get_db_connection()

    conn.execute("""
        UPDATE books
        SET status = 'rejected',
            rejected_at = CURRENT_TIMESTAMP,
            approved_at = NULL
        WHERE id = ?
    """, (book_id,))

    conn.commit()
    conn.close()

    return redirect("/librarian/pending")



@app.route("/librarian/book/<int:book_id>/edit", methods=["GET", "POST"])
def librarian_edit_book(book_id):

    if session.get("role") != "librarian":
        return "Access denied"

    conn = get_db_connection()

    # Отримуємо книгу
    book = conn.execute("""
        SELECT *
        FROM books
        WHERE id = ? AND status = 'approved'
    """, (book_id,)).fetchone()

    if book is None:
        conn.close()
        return "Book not found", 404

    # Отримуємо всі доступні жанри
    genres = conn.execute("""
        SELECT *
        FROM genres
        ORDER BY name
    """).fetchall()

    if request.method == "POST":

        selected_genres = request.form.getlist("genres")

        # Перевіряємо, що передані ID існують у таблиці genres
        valid_genre_ids = {
            str(genre["id"]) for genre in genres
        }

        if not set(selected_genres).issubset(valid_genre_ids):
            conn.close()
            return "Invalid genre selection", 400

        # Видаляємо старі зв'язки книги з жанрами
        conn.execute("""
            DELETE FROM book_genres
            WHERE book_id = ?
        """, (book_id,))

        # Додаємо вибрані жанри
        for genre_id in selected_genres:
            conn.execute("""
                INSERT INTO book_genres (book_id, genre_id)
                VALUES (?, ?)
            """, (book_id, int(genre_id)))

        conn.commit()
        conn.close()

        flash("Book genres updated successfully!", "success")

        return redirect("/librarian/books")

    # Отримуємо жанри, які вже належать книзі
    selected_genres = conn.execute("""
        SELECT genre_id
        FROM book_genres
        WHERE book_id = ?
    """, (book_id,)).fetchall()

    selected_genre_ids = {
        genre["genre_id"] for genre in selected_genres
    }

    conn.close()

    return render_template(
        "librarian_book_edit.html",
        book=book,
        genres=genres,
        selected_genre_ids=selected_genre_ids
    )




@app.route("/librarian/books")
def librarian_books():

    if session.get("role") != "librarian":
        return "Access denied"

    search_query = request.args.get("q", "").strip()

    available_fields = {
        "title": "books.title",
        "author": """
            COALESCE(
                NULLIF(users.author_name, ''),
                users.username
            )
        """,
        "email": "users.email"
    }

    selected_fields = request.args.getlist("fields")
    selected_fields = [
        field for field in selected_fields
        if field in available_fields
    ]

    if not selected_fields:
        selected_fields = list(available_fields.keys())

    conn = get_db_connection()

    sql = """
        SELECT
            books.*,
            COALESCE(
                NULLIF(users.author_name, ''),
                users.username
            ) AS author_name,
            users.email AS author_email,
            GROUP_CONCAT(DISTINCT genres.name) AS genres
        FROM books
        JOIN users ON books.author_id = users.id
        LEFT JOIN book_genres ON books.id = book_genres.book_id
        LEFT JOIN genres ON book_genres.genre_id = genres.id
        WHERE books.status = 'approved'
    """

    params = []

    if search_query:
        conditions = []

        for field in selected_fields:
            conditions.append(
                f"{available_fields[field]} LIKE ?"
            )
            params.append(f"%{search_query}%")

        sql += " AND (" + " OR ".join(conditions) + ")"

    sql += """
        GROUP BY books.id
        ORDER BY books.approved_at DESC
    """

    books = conn.execute(sql, params).fetchall()

    conn.close()

    return render_template(
        "librarian_books.html",
        books=books,
        search_query=search_query,
        search_fields=selected_fields
    )




@app.route("/api/librarian/books")
def api_librarian_books():

    if session.get("role") != "librarian":
        return jsonify({
            "success": False,
            "error": "Access denied"
        }), 403

    search = request.args.get("search", "").strip()
    genre_id = request.args.get("genre_id", "")
    author_id = request.args.get("author_id", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    status = request.args.get("status", "approved")

    conn = get_db_connection()

    query = """
        SELECT
            books.id,
            books.title,
            COALESCE(
                NULLIF(users.author_name, ''),
                users.username
            ) AS author_name,
            books.publication_date,
            books.created_at,
            books.status,
            GROUP_CONCAT(DISTINCT genres.name) AS genres
        FROM books
        JOIN users ON books.author_id = users.id
        LEFT JOIN book_genres ON books.id = book_genres.book_id
        LEFT JOIN genres ON book_genres.genre_id = genres.id
        WHERE 1 = 1
    """

    params = []

    if search:
        query += """
            AND (
                books.title LIKE ?
                OR users.username LIKE ?
                OR users.author_name LIKE ?
            )
        """
        search_value = f"%{search}%"
        params.extend([
            search_value,
            search_value,
            search_value
        ])

    if genre_id.isdigit():
        query += """
            AND (
                EXISTS (
                    SELECT 1
                    FROM book_genres bg
                    WHERE bg.book_id = books.id
                      AND bg.genre_id = ?
                )
                OR (
                    NOT EXISTS (
                        SELECT 1
                        FROM book_genres bg2
                        WHERE bg2.book_id = books.id
                    )
                    AND books.genre_id = ?
                )
            )
        """
        params.extend([int(genre_id), int(genre_id)])

    if author_id.isdigit():
        query += " AND books.author_id = ?"
        params.append(int(author_id))

    if date_from:
        query += " AND books.publication_date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND books.publication_date <= ?"
        params.append(date_to)

    if status in ["pending", "approved", "rejected"]:
        query += " AND books.status = ?"
        params.append(status)
    elif status != "all":
        conn.close()
        return jsonify({
            "success": False,
            "error": "Invalid status"
        }), 400

    query += """
        GROUP BY books.id
        ORDER BY books.created_at DESC
    """

    books = conn.execute(query, params).fetchall()

    genres = conn.execute("""
        SELECT id, name
        FROM genres
        ORDER BY name
    """).fetchall()

    authors = conn.execute("""
        SELECT DISTINCT
            users.id,
            COALESCE(
                NULLIF(users.author_name, ''),
                users.username
            ) AS name
        FROM users
        JOIN books ON books.author_id = users.id
        ORDER BY name
    """).fetchall()

    conn.close()

    return jsonify({
        "success": True,
        "total": len(books),
        "filters": {
            "search": search,
            "genre_id": genre_id,
            "author_id": author_id,
            "date_from": date_from,
            "date_to": date_to,
            "status": status
        },
        "available_filters": {
            "genres": [dict(row) for row in genres],
            "authors": [dict(row) for row in authors],
            "statuses": [
                {"value": "all", "label": "Усі статуси"},
                {"value": "pending", "label": "Очікує перевірки"},
                {"value": "approved", "label": "Схвалена"},
                {"value": "rejected", "label": "Відхилена"}
            ]
        },
        "books": [dict(row) for row in books]
    })



@app.route("/logout")
def logout():

    session.clear()
    flash("You have been logged out. Please register or log in to continue.")

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)