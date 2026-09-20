import sqlite3

db_path = r"D:\Users\User\Desktop\Something\Learning\online-library\database\library.db"
con = sqlite3.connect(db_path)

cursor  = con.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS genres(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT UNIQUE NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS books(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    title TEXT  NOT NULL,
    description TEXT,
    author_id INTEGER NOT NULL,
    genre_id  INTEGER NOT NULL,
    file_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (author_id) REFERENCES users(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    reader_id INTEGER NOT NULL,
    rating  INTEGER CHECK(rating >=1 AND rating <= 5),
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reader_id) REFERENCES users(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
    )
""")

#cursor.execute("""
#    INSERT INTO users(username, email, password_hash, role)
#    VALUES('Kava', 'kava@gmail.com', '12345678', 'reader')
    
#""")
#cursor.execute("""
#    INSERT INTO books(title, description, author_id, genre_id)
#    VALUES('Harry Potter', 'A fantasy book', 1, 1)
#""")

cursor.execute("""
    INSERT OR IGNORE INTO genres(name)
    VALUES('Fantasy')
""")

#cursor.execute("""
   # ALTER TABLE books
   # ADD COLUMN status TEXT DEFAULT 'pending';
#""")
cursor.execute("""
    SELECT id, title, status FROM books;
""")



cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_genres (
        book_id INTEGER NOT NULL,
        genre_id INTEGER NOT NULL,

        PRIMARY KEY (book_id, genre_id),

        FOREIGN KEY (book_id) REFERENCES books(id),
        FOREIGN KEY (genre_id) REFERENCES genres(id)
    )
""")
cursor.execute("""
    INSERT OR IGNORE INTO book_genres (book_id, genre_id)
    SELECT id, genre_id
    FROM books
    WHERE genre_id IS NOT NULL
""")
#----------------------------
# переношу зі старої дб у нову без unique
cursor.execute("PRAGMA foreign_keys = OFF")

cursor.execute("""
    CREATE TABLE books_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        author_id INTEGER NOT NULL,
        genre_id INTEGER NOT NULL,
        file_path TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending',

        FOREIGN KEY (author_id) REFERENCES users(id),
        FOREIGN KEY (genre_id) REFERENCES genres(id)
    )
""")

cursor.execute("""
    INSERT INTO books_new
    (id, title, description, author_id, genre_id, file_path, created_at, status)
    SELECT
        id, title, description, author_id, genre_id, file_path, created_at, status
    FROM books
""")

cursor.execute("DROP TABLE books")

cursor.execute("""
    ALTER TABLE books_new
    RENAME TO books
""")

cursor.execute("PRAGMA foreign_keys = ON")

#------------------------------------

cursor.executemany("""
    INSERT OR IGNORE INTO genres (name)
    VALUES (?)
""", [
    ('Fantasy',),
    ('Science Fiction',),
    ('Adventure',),
    ('Mystery',),
    ('Thriller',),
    ('Horror',),
    ('Romance',),
    ('Drama',),
    ('Historical Fiction',),
    ('Detective',),
    ('Crime',),
    ('Comedy',),
    ('Biography',),
    ('Autobiography',),
    ('History',),
    ('Philosophy',),
    ('Psychology',),
    ('Self-Help',),
    ('Poetry',),
    ('Classic',),
    ('Young Adult',),
    ('Children''s',),
    ('Dystopian',),
    ('Action',),
    ('Literary Fiction',)
])

cursor.execute("""
    ALTER TABLE books ADD COLUMN approved_at DATETIME
""")

cursor.execute("""
    ALTER TABLE books ADD COLUMN rejected_at DATETIME
""")

con.commit()

cursor.execute("PRAGMA table_info(books)")

columns = cursor.fetchall()

for column in columns:
    print(column)

#cursor.execute("""
#    SELECT sql
 #   FROM sqlite_master
 #   WHERE type = 'table'
 #   AND name = 'books';
#""")

#result = cursor.fetchone()

#print("BOOKS TABLE:")
#print(result)


#cursor.execute("""
#    SELECT sql
#    FROM sqlite_master
 #   WHERE type = 'table'
#    AND name = 'reviews';
#""")

#result = cursor.fetchone()

#print("REVIEWS TABLE:")
#print(result)

cursor.execute("SELECT * FROM genres")

print("GENRES:")
for row in cursor.fetchall():
    print(row)





cursor.execute("SELECT * FROM book_genres")
print("BOOK_GENRES:")
for row in cursor.fetchall():
    print(row)


cursor.execute("SELECT * FROM users")
print("USERS:")

rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.execute("SELECT * FROM genres")
print("GENRES:")

rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.execute("SELECT * FROM books")
print("BOOKS:")

rows = cursor.fetchall()

for row in rows:
    print(row)

con.close()

print("Users table created!")