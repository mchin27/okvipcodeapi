from fastapi import APIRouter
from db.database import database
from db.models import apply_code_tbl, players_lock_tbl
import datetime

router = APIRouter()

@router.get("/api/today-codes/{site}")
async def get_today_codes(site: str):
    today = datetime.date.today()
    query = apply_code_tbl.select().where(
        (apply_code_tbl.c.site_name == site) &
        (apply_code_tbl.c.date == today) &
        (apply_code_tbl.c.is_delete == False)
    )
    rows = await database.fetch_all(query)
    return {"players": rows}


@router.get("/api/today-locks/{site}")
async def get_today_locks(site: str):
    today = datetime.date.today()
    query = players_lock_tbl.select().where(
        (players_lock_tbl.c.site_name == site) &
        (players_lock_tbl.c.created_at >= today) &
        (players_lock_tbl.c.is_delete == False)
    )
    rows = await database.fetch_all(query)
    return {"playersLock": rows}