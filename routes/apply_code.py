from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.database import database, DATABASE_URL
from sqlalchemy import create_engine, MetaData, select, insert
from datetime import datetime, timedelta
from collections import defaultdict

router = APIRouter()

# Load DB metadata
engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

# Reflect tables
promo_code_applies = metadata.tables["promo_code_applies"]
player_package_purchases = metadata.tables["player_package_purchases"]
players = metadata.tables["players"]
players_lock = metadata.tables["players_lock"]
sites = metadata.tables["sites"]

# -------------------------------
# ✅ 1. POST /players-apply-code
# -------------------------------
class ApplyCodeRequest(BaseModel):
    site: str
    player: str
    promo_code: str
    point: float

@router.post("/players-apply-code")
async def save_apply_code(data: ApplyCodeRequest):
    # หา site_id จาก site_key
    site_query = select(sites.c.id).where(sites.c.site_key == data.site)
    site_result = await database.fetch_one(site_query)
    if not site_result:
        raise HTTPException(status_code=404, detail="Site not found")
    site_id = site_result.id

    # หา player_id และสถานะ is_unlimited_code โดยกรอง site_id ด้วย
    player_query = select(players.c.id, players.c.is_unlimited_code).where(
        (players.c.username == data.player) &
        (players.c.site_id == site_id)
    )
    player_result = await database.fetch_one(player_query)
    if not player_result:
        raise HTTPException(status_code=404, detail="Player not found in this site")

    player_id = player_result.id
    is_unlimited = bool(player_result.is_unlimited_code)

    purchase_id = None
    # ถ้าไม่ใช่ unlimited ต้องมี package purchase
    if not is_unlimited:
        purchase_query = (
            select(player_package_purchases.c.id)
            .where(player_package_purchases.c.player_id == player_id)
            .order_by(player_package_purchases.c.purchase_time.desc())
            .limit(1)
        )
        purchase_result = await database.fetch_one(purchase_query)
        if not purchase_result:
            raise HTTPException(status_code=404, detail="No package purchase found for this player")
        purchase_id = purchase_result.id

    now = datetime.utcnow()
    lock_minutes = 1440  # 24 ชั่วโมง

    # Insert apply code (อนุญาตให้ purchase_id เป็น None ถ้า unlimited)
    stmt_apply = insert(promo_code_applies).values(
        purchase_id=purchase_id,
        promo_code=data.promo_code,
        point=data.point,
        status="success",
        apply_time=now
    )

    # Lock player
    stmt_lock = insert(players_lock).values(
        player_id=player_id,
        timelock=now,
        lock_time_minutes=lock_minutes,
        lock_message="เกินสิทธิ์รายวัน",
        lock_code=1
    )

    try:
        async with database.transaction():
            await database.execute(stmt_apply)
            await database.execute(stmt_lock)
        return {"message": f"Promo code applied and player locked successfully in site {data.site}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# ✅ 2. POST /players-lock
# -------------------------------
class LockPlayerRequest(BaseModel):
    site: str
    username: str
    lock_minutes: int = 1440  # Default 24 hours
    lock_message: str = "ถูกล็อกโดยแอดมิน"
    lock_code: int = 0

@router.post("/players-lock")
async def lock_player(data: LockPlayerRequest):
    # หา site_id จาก site key
    site_query = select(sites.c.id).where(sites.c.site_key == data.site)
    site_result = await database.fetch_one(site_query)
    if not site_result:
        raise HTTPException(status_code=404, detail="Site not found")
    site_id = site_result.id

    # หา player_id โดย filter site_id + username
    player_query = select(players.c.id).where(
        (players.c.username == data.username) &
        (players.c.site_id == site_id)
    )
    player_result = await database.fetch_one(player_query)
    if not player_result:
        raise HTTPException(status_code=404, detail="Player not found in this site")
    player_id = player_result.id

    now = datetime.utcnow()

    stmt = insert(players_lock).values(
        player_id=player_id,
        timelock=now,
        lock_time_minutes=data.lock_minutes,
        lock_message=data.lock_message,
        lock_code=data.lock_code
    )

    try:
        await database.execute(stmt)
        return {"message": f"Player {data.username} locked for {data.lock_minutes} minutes in site {data.site}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# ✅ 3. GET /players-apply-code (no playersLock)
# -------------------------------
@router.get("/players-apply-code")
async def get_apply_code_today():
    j = (
        promo_code_applies
        .join(player_package_purchases, promo_code_applies.c.purchase_id == player_package_purchases.c.id)
        .join(players, player_package_purchases.c.player_id == players.c.id)
        .join(sites, players.c.site_id == sites.c.id)
    )

    stmt = (
        select(
            promo_code_applies.c.promo_code,
            promo_code_applies.c.apply_time,
            promo_code_applies.c.status,
            promo_code_applies.c.point,
            players.c.username.label("player"),
            sites.c.site_key.label("site")
        )
        .select_from(j)
        .order_by(promo_code_applies.c.apply_time.desc())
    )

    results = await database.fetch_all(stmt)

    grouped_data = defaultdict(lambda: {"players": [], "playersLock": []})
    expire_ms = 24 * 60 * 60 * 1000  # 24 ชั่วโมง

    for row in results:
        ts_ms = int(row["apply_time"].timestamp() * 1000)
        grouped_data[row["site"]]["players"].append({
            "promo_code": row["promo_code"],
            "time": ts_ms,
            "time_limit": ts_ms + expire_ms,
            "status": row["status"],
            "player": row["player"],
            "point": float(row["point"])
        })

    return {
        "apply_code_today": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            **grouped_data
        }
    }


# -------------------------------
# ✅ 4. GET /players-lock
# -------------------------------
@router.get("/players-lock")
async def get_all_locked_players():
    now = datetime.utcnow()

    stmt = (
        select(
            players.c.site_id,
            players.c.username.label("player"),
            players_lock.c.timelock,
            players_lock.c.lock_time_minutes,
            players_lock.c.lock_message,
            players_lock.c.lock_code,
            sites.c.site_key.label("site")
        )
        .select_from(
            players_lock
            .join(players, players_lock.c.player_id == players.c.id)
            .join(sites, players.c.site_id == sites.c.id)
        )
        .order_by(players_lock.c.timelock.desc())
    )

    locks = await database.fetch_all(stmt)

    result = []
    for lock in locks:
        timelock = lock["timelock"]
        time_limit = timelock + timedelta(minutes=lock["lock_time_minutes"])
        result.append({
            "site": lock["site"],
            "player": lock["player"],
            "timelock": int(timelock.timestamp() * 1000),
            "time_limit": int(time_limit.timestamp() * 1000),
            "lock_message": lock["lock_message"],
            "lock_code": lock["lock_code"],
            "active": time_limit > now
        })

    return {"playersLock": result}
