from pathlib import Path
import shutil, sqlite3, tempfile


ORIGINAL = Path(__file__).resolve().parent / "books.db"


TMP_DIR = Path("/tmp") if Path("/tmp").exists() else Path(tempfile.gettempdir())
WORKING = TMP_DIR / "app.db"

def prepare_db():
    if not WORKING.exists():
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        if ORIGINAL.exists():
            shutil.copy(ORIGINAL, WORKING)
        else:
           
            conn = sqlite3.connect(WORKING)
            with conn:
                conn.execute("""
                  CREATE TABLE IF NOT EXISTS books(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    read_on TEXT,
                    rating INTEGER,
                    created_at TEXT
                  )
                """)
            conn.close()

def get_conn():
    conn = sqlite3.connect(WORKING, check_same_thread=False, timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

