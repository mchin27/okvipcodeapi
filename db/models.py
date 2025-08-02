from sqlalchemy import (
    Table, Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Float, Date
)
from db.database import metadata  # สมมติคุณมี metadata ที่ import จาก database.py

# ตารางเก็บข้อมูลผู้เล่น
players_tbl = Table(
    "players_tbl",
    metadata,
    Column("players_name", String, primary_key=True),  # unique player name
    Column("telegram_id", Integer, nullable=True),
    Column("site_name", String, nullable=True),
    Column("telegram_name", String, nullable=True),
    Column("created_at", TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP"),
    Column("updated_at", TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP"),
    Column("is_delete", Boolean, nullable=False, default=False),
)

# ตารางล็อคผู้เล่น
players_lock_tbl = Table(
    "players_lock_tbl",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("player_name", String, ForeignKey("players_tbl.players_name", ondelete="CASCADE"), nullable=False),
    Column("site_name", String, nullable=False),
    Column("lock_message", String, nullable=True),
    Column("lock_time", Integer, nullable=False),  # เวลา lock เป็น milliseconds หรือ วินาที
    Column("timelock", TIMESTAMP, nullable=False),  # เวลาที่ lock
    Column("created_at", TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP"),
    Column("updated_at", TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP"),
    Column("is_delete", Boolean, nullable=False, default=False),
)

# ตาราง player pool
player_pool_tbl = Table(
    "player_pool_tbl",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("player_name", String, ForeignKey("players_tbl.players_name", ondelete="CASCADE"), nullable=False),
    Column("site_name", String, nullable=False),
    Column("pool_group", String, nullable=False),  # เช่น 'high', 'mid', 'low'
)

# ตาราง apply code log
apply_code_tbl = Table(
    "apply_code_tbl",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("promo_code", String, nullable=False),
    Column("site_name", String, nullable=False),
    Column("date", Date, nullable=False),  # วันเวลาเก็บ log
    Column("player_name", String, ForeignKey("players_tbl.players_name", ondelete="CASCADE"), nullable=False),
    Column("point", Float, nullable=False),
    Column("status", String, nullable=False),  # เช่น success, failed
    Column("time", TIMESTAMP, nullable=False),  # เวลา log เกิดขึ้น
    Column("time_limit", TIMESTAMP, nullable=False),  # เวลาหมดอายุ
    Column("is_delete", Boolean, nullable=False, default=False),
    Column("created_at", TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP"),
    Column("updated_at", TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP"),
)
