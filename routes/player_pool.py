from fastapi import APIRouter
from db.database import database, DATABASE_URL
from sqlalchemy import Table, MetaData, create_engine, select
from typing import Dict, List

router = APIRouter()

engine = create_engine(DATABASE_URL)
metadata = MetaData()

available_players_by_site_tier = Table(
    "available_players_by_site_tier", metadata, autoload_with=engine
)

TIERS = {"very_high", "high", "mid", "low"}

@router.get("/player-pools")
async def get_player_pools(limit: int = 1000, offset: int = 0) -> Dict[str, Dict[str, List[str]]]:
    query = select(available_players_by_site_tier).limit(limit).offset(offset)
    result = await database.fetch_all(query)

    pools: Dict[str, Dict[str, List[str]]] = {}

    for row in result:
        site = row["site_key"]
        tier = row["tier_name"]
        username = row["username"]

        if site not in pools:
            pools[site] = {t: [] for t in TIERS}
            pools[site]["all"] = []

        # เพิ่ม username เฉพาะกรณี tier อยู่ใน TIERS
        if tier in TIERS and username not in pools[site][tier]:
            pools[site][tier].append(username)

        if username not in pools[site]["all"]:
            pools[site]["all"].append(username)

    return pools



