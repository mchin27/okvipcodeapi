from fastapi import APIRouter
from db.database import database
from db.models import player_pool_tbl, players_tbl
from sqlalchemy import select
from collections import defaultdict

router = APIRouter()

@router.get("/api/playerPools")
async def get_player_pools():
    query = (
        select([
            player_pool_tbl.c.player_name,
            player_pool_tbl.c.site_name,
            player_pool_tbl.c.pool_group
        ])
        .select_from(
            player_pool_tbl.join(players_tbl, player_pool_tbl.c.player_name == players_tbl.c.players_name)
        )
        .order_by(player_pool_tbl.c.site_name, player_pool_tbl.c.pool_group, player_pool_tbl.c.player_name)
    )
    rows = await database.fetch_all(query)

    result = defaultdict(lambda: {"high": [], "mid": [], "low": []})

    for row in rows:
        site = row['site_name']
        group = row['pool_group']
        player = row['player_name']
        result[site][group].append(player)

    return dict(result)
