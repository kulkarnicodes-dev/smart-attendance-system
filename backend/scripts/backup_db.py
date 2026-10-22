"""Copy the SQLite database to backend/backups/ with a timestamp:  python scripts/backup_db.py
(For MySQL use:  mysqldump -u root -p smart_attendance > backup.sql)"""
import shutil
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings, BASE_DIR

url = settings.DATABASE_URL
if not url.startswith("sqlite:///"):
    sys.exit("Not a SQLite database. Use mysqldump for MySQL.")
src = Path(url.replace("sqlite:///", "", 1))
src = src if src.is_absolute() else BASE_DIR / src
dest_dir = BASE_DIR / "backups"
dest_dir.mkdir(exist_ok=True)
dest = dest_dir / f"attendance-{datetime.now():%Y%m%d-%H%M%S}.db"
shutil.copy2(src, dest)
print("Backup written:", dest)
