from fastapi import APIRouter, Query
from db.database import database, DATABASE_URL
from sqlalchemy import Table, MetaData, create_engine, select

router = APIRouter()

# ✅ สร้าง engine และ metadata
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# ✅ โหลดตารางจาก DB
packages = Table("packages", metadata, autoload_with=engine)
sites = Table("sites", metadata, autoload_with=engine)

@router.get("/packages")
async def get_packages(
    limit: int = Query(100, ge=1, le=500), 
    offset: int = Query(0, ge=0)
):
    query = select(packages).limit(limit).offset(offset)
    result = await database.fetch_all(query)
    return {"packages": [dict(row._mapping) for row in result]}

@router.get("/sites")
async def get_sites(
    limit: int = Query(100, ge=1, le=500), 
    offset: int = Query(0, ge=0)
):
    query = select(sites).limit(limit).offset(offset)
    result = await database.fetch_all(query)
    return {"sites": [dict(row._mapping) for row in result]}
