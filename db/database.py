# db/database.py
from databases import Database
import sqlalchemy

DATABASE_URL = "postgresql://ai_db_user:zFI2fpddtwe98uFpQLHtU0cbcacM3N7R@dpg-d27haffdiees73ck1b1g-a.oregon-postgres.render.com/ai_code_db"

database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
