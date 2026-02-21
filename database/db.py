import aiosqlite
import json
from datetime import datetime

DB_PATH = "kinobot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                join_date TEXT,
                watched_count INTEGER DEFAULT 0,
                rating_count INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                year TEXT,
                genre TEXT,
                file_id TEXT,
                thumb_file_id TEXT,
                code TEXT UNIQUE,
                views INTEGER DEFAULT 0,
                total_rating REAL DEFAULT 0,
                rating_count INTEGER DEFAULT 0,
                channel_message_id INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                code TEXT UNIQUE,
                year TEXT,
                genre TEXT,
                thumb_file_id TEXT,
                channel_message_id INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_id INTEGER,
                season INTEGER,
                episode INTEGER,
                file_id TEXT,
                FOREIGN KEY (serial_id) REFERENCES series(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content_id INTEGER,
                content_type TEXT,
                rating INTEGER,
                UNIQUE(user_id, content_id, content_type)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT,
                title TEXT,
                channel_type TEXT,
                link TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_sessions (
                user_id INTEGER PRIMARY KEY,
                authenticated INTEGER DEFAULT 0
            )
        """)
        await db.commit()


# ===================== USERS =====================
async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, full_name, join_date)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, full_name, datetime.now().strftime("%Y-%m-%d")))
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cursor:
            return await cursor.fetchone()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            return await cursor.fetchall()


async def increment_watched(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET watched_count = watched_count + 1 WHERE user_id=?", (user_id,))
        await db.commit()


# ===================== MOVIES =====================
async def add_movie(name, description, year, genre, file_id, thumb_file_id, code, created_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO movies (name, description, year, genre, file_id, thumb_file_id, code, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, year, genre, file_id, thumb_file_id, code, created_at))
        await db.commit()


async def get_movie_by_code(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM movies WHERE code=?", (code,)) as cursor:
            return await cursor.fetchone()


async def get_all_movies():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM movies ORDER BY id DESC") as cursor:
            return await cursor.fetchall()


async def delete_movie(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM movies WHERE code=?", (code,))
        await db.commit()


async def increment_movie_views(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET views = views + 1 WHERE code=?", (code,))
        await db.commit()


async def update_movie_rating(code: str, rating: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE movies SET 
                total_rating = total_rating + ?,
                rating_count = rating_count + 1
            WHERE code=?
        """, (rating, code))
        await db.commit()


async def update_movie_channel_msg(code: str, msg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET channel_message_id=? WHERE code=?", (msg_id, code))
        await db.commit()


async def get_top_movies(limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM movies ORDER BY views DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM movies") as c:
            movies = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM series") as c:
            series = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM ratings") as c:
            ratings = (await c.fetchone())[0]
        async with db.execute("SELECT name, views FROM movies ORDER BY views DESC LIMIT 1") as c:
            top = await c.fetchone()
        return {
            "users": users,
            "movies": movies,
            "series": series,
            "ratings": ratings,
            "top_movie": top
        }


# ===================== SERIES =====================
async def add_series(name, description, code, year, genre, thumb_file_id, created_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO series (name, description, code, year, genre, thumb_file_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, description, code, year, genre, thumb_file_id, created_at))
        await db.commit()


async def get_series_by_code(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM series WHERE code=?", (code,)) as cursor:
            return await cursor.fetchone()


async def get_all_series():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM series ORDER BY id DESC") as cursor:
            return await cursor.fetchall()


async def delete_series(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        serial = await get_series_by_code(code)
        if serial:
            await db.execute("DELETE FROM episodes WHERE serial_id=?", (serial["id"],))
        await db.execute("DELETE FROM series WHERE code=?", (code,))
        await db.commit()


async def add_episode(serial_id, season, episode, file_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO episodes (serial_id, season, episode, file_id)
            VALUES (?, ?, ?, ?)
        """, (serial_id, season, episode, file_id))
        await db.commit()


async def get_episodes(serial_id, season=None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if season:
            async with db.execute(
                "SELECT * FROM episodes WHERE serial_id=? AND season=? ORDER BY episode",
                (serial_id, season)
            ) as cursor:
                return await cursor.fetchall()
        else:
            async with db.execute(
                "SELECT DISTINCT season FROM episodes WHERE serial_id=? ORDER BY season",
                (serial_id,)
            ) as cursor:
                return await cursor.fetchall()


# ===================== RATINGS =====================
async def add_rating(user_id, content_id, content_type, rating):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO ratings (user_id, content_id, content_type, rating)
                VALUES (?, ?, ?, ?)
            """, (user_id, content_id, content_type, rating))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def has_rated(user_id, content_id, content_type):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM ratings WHERE user_id=? AND content_id=? AND content_type=?",
            (user_id, content_id, content_type)
        ) as cursor:
            return await cursor.fetchone() is not None


# ===================== CHANNELS =====================
async def add_channel(channel_id, title, channel_type, link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO channels (channel_id, title, channel_type, link)
            VALUES (?, ?, ?, ?)
        """, (channel_id, title, channel_type, link))
        await db.commit()


async def get_all_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels") as cursor:
            return await cursor.fetchall()


async def delete_channel(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
        await db.commit()


# ===================== ADMIN SESSIONS =====================
async def set_admin_auth(user_id: int, status: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO admin_sessions (user_id, authenticated) VALUES (?, ?)
        """, (user_id, status))
        await db.commit()


async def is_admin_authenticated(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT authenticated FROM admin_sessions WHERE user_id=?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row and row[0] == 1
