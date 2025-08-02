from databases import Database
import sqlalchemy

DATABASE_URL = "postgresql://procode_ai:oCEyeSKwqqEgcn5A3Qbs20lFhJdgWo29@dpg-d1qrbgndiees73f7tl2g-a.oregon-postgres.render.com/promocode_ai"

database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
