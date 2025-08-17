# routes/callback_data.py
from fastapi import APIRouter, Request
from routes.payment import callback_mapping, mask_username, send_message, TELEGRAM_API_URL
from db.database import database
from db.models import package_orders, players
from sqlalchemy import select
from datetime import datetime
import httpx

router = APIRouter()

async def answer_callback_query(callback_query_id: str, text: str = None):
    """ตอบ callback query เพื่อปิด loading circle"""
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id}
    if text:
        data["text"] = text
    async with httpx.AsyncClient() as client:
        await client.post(url, json=data)

@router.post("/api/telegram/callback")
async def telegram_callback(request: Request):
    """รับ callback_query จาก Telegram"""
    data = await request.json()
    callback_query = data.get("callback_query", {})
    callback_data = callback_query.get("data")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    callback_query_id = callback_query.get("id")

    if not callback_data or callback_data not in callback_mapping:
        return {"ok": False}

    info = callback_mapping.pop(callback_data)
    user = info["user"]
    package = info["package"]
    price = info["price"]
    site_key = info["site"]

    player_row = await database.fetch_one(select(players.c.id).where(players.c.username == user))
    if not player_row:
        return {"ok": False}

    player_id = player_row.id

    order = await database.fetch_one(
        select(package_orders)
        .where(
            (package_orders.c.status == "pending") &
            (package_orders.c.player_id == player_id) &
            (package_orders.c.slip_url != None)
        )
    )

    if order:
        await database.execute(
            package_orders.update()
            .where(package_orders.c.id == order.id)
            .values(status="approved", approved_time=datetime.utcnow())
        )

        caption = (
            f"\U00002705 <b>คำสั่งซื้ออนุมัติแล้ว</b>\n"
            f"📃 เลขที่คำสั่งซื้อ: <code>{order.order_no}</code>\n"
            f"📦 แพ็กเกจ: {package}\n"
            f"💰 ราคา: {price} บาท\n"
            f"👤 ยูสเซอร์: {mask_username(user)}"
        )
        if chat_id:
            await send_message(chat_id, caption)

    if callback_query_id:
        await answer_callback_query(callback_query_id, "✅ อนุมัติเรียบร้อยแล้ว")

    return {"ok": True}
