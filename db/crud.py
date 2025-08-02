from .database import database
from .models import apply_code_tbl
import datetime

async def insert_apply_code():
    query = apply_code_tbl.insert().values(
        date=datetime.date.today(),
        site_name="thai_jun88k36",
        promo_code="ZHBH0YL",
        time=1752539640361,
        time_limit=1752626040361,
        status="success",
        player_name="manus9331",
        point=21.88
    )
    await database.execute(query)
