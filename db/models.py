from sqlalchemy import (
    Table, Column, Integer, String, Boolean, ForeignKey,
    TIMESTAMP, Text, Numeric, func
)
from datetime import datetime

from db.database import metadata

players = Table(
    "players",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, nullable=False),
    Column("site_id", Integer, ForeignKey("sites.id")),
    Column("first_name", String),
    Column("last_name", String),
    Column("phone", String),
    Column("email", String),
    Column("is_active", Boolean, default=True),
    Column("is_unlimited_code", Boolean, default=True),
    Column("telegram_id", String),  # 🔄 changed from Integer → String
)

packages = Table(
    "packages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("description", Text),
    Column("price", Numeric),
    Column("sale_price", Numeric),
    Column("code_limit", Integer),
    Column("site_id", Integer, ForeignKey("sites.id")),
    Column("logo_url", Text),
    Column("is_active", Boolean, default=True),
)

package_orders = Table(
    "package_orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("order_no", String, unique=True, nullable=False),
    Column("player_id", Integer, ForeignKey("players.id")),
    Column("package_id", Integer, ForeignKey("packages.id")),
    Column("slip_url", Text),
    Column("notify_telegram", Boolean, default=False),
    Column("telegram_id", String),
    Column("status", String, default="pending"),
    Column("price", Numeric),  # ✅ เพิ่มช่องเก็บราคา
    Column("created_at", TIMESTAMP, default=datetime.utcnow),  # ✅ เพิ่มเวลาสร้าง
    Column("order_time", TIMESTAMP, default=datetime.utcnow),
    Column("approved_time", TIMESTAMP)
)


player_package_purchases = Table(
    "player_package_purchases",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id")),
    Column("package_id", Integer, ForeignKey("packages.id")),
    Column("purchase_time", TIMESTAMP, server_default=func.now()),
)

site_player_tiers = Table(
    "site_player_tiers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("site_id", Integer, ForeignKey("sites.id")),
    Column("player_id", Integer, ForeignKey("players.id")),
    Column("tier_id", Integer, ForeignKey("tiers.id")),
)

tiers = Table(
    "tiers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
)

package_tiers = Table(
    "package_tiers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("package_id", Integer, ForeignKey("packages.id")),
    Column("tier_id", Integer, ForeignKey("tiers.id")),
)

sites = Table(
    "sites",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("site_key", String(50), unique=True, nullable=False),
    Column("name", String(100), nullable=False),
)
