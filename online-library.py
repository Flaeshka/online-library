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
    title TEXT UNIQUE NOT NULL,
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



con.commit()

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