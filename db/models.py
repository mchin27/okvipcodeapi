from sqlalchemy import Table, Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, Text, Numeric
from db.database import metadata

players = Table(
    "players",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, nullable=False),
    # other columns...
)

packages = Table(
    "packages",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    # other columns...
)

package_orders = Table(
    "package_orders",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id")),
    Column("package_id", Integer, ForeignKey("packages.id")),
    # other columns...
)

player_package_purchases = Table(
    "player_package_purchases",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id")),
    Column("package_id", Integer, ForeignKey("packages.id")),
    # other columns...
)

site_player_tiers = Table(
    "site_player_tiers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id")),
    Column("tier_id", Integer, ForeignKey("tiers.id")),
    # other columns...
)

tiers = Table(
    "tiers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    # other columns...
)

package_tiers = Table(
    "package_tiers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("package_id", Integer, ForeignKey("packages.id")),
    Column("tier_id", Integer, ForeignKey("tiers.id")),
    # other columns...
)


sites = Table(
    "sites",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("site_key", String(50), unique=True, nullable=False),
    Column("name", String(100), nullable=False)
)