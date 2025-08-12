from fastapi import APIRouter, Query
from db.database import database, DATABASE_URL
from sqlalchemy import Table, MetaData, create_engine, select

router = APIRouter()

# ✅ สร้าง engine และ metadata เพื่อโหลด view จาก database
engine = create_engine(DATABASE_URL)
metadata = MetaData()


# ✅ โหลดตาราง packages จาก database (autoload จากชื่อ table/view)
packages = Table("packages", metadata, autoload_with=engine)

@router.get("/packages")
async def get_packages(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    query = select(packages).limit(limit).offset(offset)
    result = await database.fetch_all(query)
    return {"packages": [dict(row) for row in result]}