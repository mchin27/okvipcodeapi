import os
import httpx
import json
import shutil
import uuid
import random
import string
import hashlib
from fastapi import APIRouter, UploadFile, Form, File, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from db.database import database
from sqlalchemy import select
from datetime import datetime
from db.models import sites, players, packages, package_orders

load_dotenv()

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_PAYMENT = os.getenv("CHANNEL_PAYMENT")
CHANNEL_CODE = os.getenv("CHANNEL_CODE")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ------------------------
# Memory store สำหรับ callback_data mapping
# ------------------------
callback_mapping = {}  # callback_data -> dict(user, package, price, site)

# ------------------------
# Utility functions
# ------------------------

def mask_username(username: str) -> str:
    """ซ่อน username บางส่วน"""
    if len(username) <= 5:
        return username
    return username[:3] + '*' * (len(username) - 5) + username[-2:]

def generate_order_no(length: int = 10) -> str:
    """สุ่มเลขที่คำสั่งซื้อ"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_callback_data(user, package, price, site):
    """สร้าง callback_data hash-safe ขนาด 64 chars"""
    raw = f"{user}|{package}|{price}|{site}"
    hash_str = hashlib.sha256(raw.encode()).hexdigest()[:64]
    callback_mapping[hash_str] = {"user": user, "package": package, "price": price, "site": site}
    return hash_str

async def send_photo(chat_id: str, caption: str, file_path: str, buttons: list = None):
    """ส่งรูปภาพไป Telegram"""
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    files = {
        "photo": (os.path.basename(file_path), open(file_path, "rb"),
                  "image/png" if file_path.endswith(".png") else "image/jpeg")
    }
    data = {"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"}
    if buttons:
        reply_markup = {
            "inline_keyboard": [
                [{"text": b["text"], "callback_data": b["callback_data"]} for b in buttons]
            ]
        }
        data["reply_markup"] = json.dumps(reply_markup)
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, files=files)
        response.raise_for_status()

async def send_message(chat_id: str, message: str):
    """ส่งข้อความไป Telegram"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {"chat_id": str(chat_id), "text": message, "parse_mode": "HTML"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        response.raise_for_status()

async def answer_callback_query(callback_query_id: str, text: str = None):
    """ตอบ callback query เพื่อปิด loading circle"""
    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id}
    if text:
        data["text"] = text
    async with httpx.AsyncClient() as client:
        await client.post(url, json=data)

# ------------------------
# API Routes
# ------------------------

@router.post("/api/submit-slip")
async def submit_payment(
    package_id: str = Form(...),
    package: str = Form(...),
    price: str = Form(...),
    site: str = Form(...),
    user: str = Form(...),
    slip: UploadFile = File(...),
    notifyTelegram: bool = Form(False),
    telegramId: str = Form(None)
):
    """รับสลิปการโอนเงินจากผู้ใช้"""
    upload_folder = "./uploads/slip"
    os.makedirs(upload_folder, exist_ok=True)
    file_ext = os.path.splitext(slip.filename)[1]
    saved_filename = f"{uuid.uuid4()}{file_ext}"
    saved_filepath = os.path.join(upload_folder, saved_filename)
    with open(saved_filepath, "wb") as buffer:
        shutil.copyfileobj(slip.file, buffer)

    order_no = generate_order_no()

    caption_main = (
        f"\U0001F4E6 <b>คำสั่งซื้อใหม่</b>\n"
        f"\U0001F3C3 เลขที่คำสั่งซื้อ: <code>{order_no}</code>\n"
        f"\U0001F4E6 แพ็กเกจ: {package}\n"
        f"\U0001F4B0 ราคา: {price} บาท\n"
        f"🌐 ไซต์: {site}\n"
        f"\U0001F464 ยูสเซอร์: {user}"
    )
    caption_status = (
        f"⏳ <b>สถานะรอตรวจสอบ</b>\n"
        f"📃 เลขที่คำสั่งซื้อ: <code>{order_no}</code>\n"
        f"📦 แพ็กเกจ: {package}\n"
        f"💰 ราคา: {price} บาท\n"
        f"🌐 ไซต์: {site}\n"
        f"👤 ยูสเซอร์: {mask_username(user)}"
    )

    try:
        if TELEGRAM_BOT_TOKEN and CHANNEL_PAYMENT:
            callback_data = generate_callback_data(user, package, price, site)
            buttons = [{"text": "✅ อนุมัติแพ็กเกจ", "callback_data": callback_data}]
            await send_photo(CHANNEL_PAYMENT, caption_main, saved_filepath, buttons)
        if TELEGRAM_BOT_TOKEN and CHANNEL_CODE:
            await send_message(CHANNEL_CODE, caption_status)
    except Exception as e:
        print("⚠️ ไม่สามารถส่งข้อมูลไปยัง Telegram channel:", e)

    if notifyTelegram and telegramId:
        try:
            await send_photo(telegramId, caption_main, saved_filepath)
        except Exception as e:
            print("⚠️ ไม่สามารถส่งข้อมูลไปยัง Telegram user:", e)

    site_map = {"jun88": "thai_jun88k36", "789bet": "thai_789bet"}
    site = site_map.get(site, site)
    site_result = await database.fetch_one(select(sites.c.id).where(sites.c.site_key == site))
    if not site_result:
        return JSONResponse({"status": "error", "message": f"ไม่พบไซต์ {site}"})
    site_id = site_result.id

    player_result = await database.fetch_one(
        select(players.c.id).where((players.c.username == user) & (players.c.site_id == site_id))
    )
    if not player_result:
        new_player_id = await database.execute(players.insert().values(username=user, site_id=site_id))
    else:
        new_player_id = player_result.id

    package_result = await database.fetch_one(select(packages.c.id).where(packages.c.name == package))
    if not package_result:
        return JSONResponse({"status": "error", "message": "ไม่พบแพ็กเกจ"})

    await database.execute(package_orders.insert().values(
        order_no=order_no,
        player_id=new_player_id,
        package_id=package_result.id,
        slip_url=saved_filepath,
        notify_telegram=notifyTelegram,
        telegram_id=telegramId,
        status="pending",
        price=price,
        created_at=datetime.utcnow()
    ))

    return JSONResponse({"status": "success", "message": "ข้อมูลถูกส่งเรียบร้อยแล้ว", "order_no": order_no})

# ------------------------
# Approve via order_no
# ------------------------
@router.post("/api/approve-order")
async def approve_order(order_no: str = Form(...)):
    order = await database.fetch_one(select(package_orders).where(package_orders.c.order_no == order_no))
    if not order:
        return JSONResponse({"status": "error", "message": "ไม่พบคำสั่งซื้อ"})

    await database.execute(
        package_orders.update().where(package_orders.c.order_no == order_no)
        .values(status="approved", approved_time=datetime.utcnow())
    )

    player = await database.fetch_one(select(players.c.username).where(players.c.id == order.player_id))
    package = await database.fetch_one(select(packages.c.name).where(packages.c.id == order.package_id))

    caption = (
        f"\U00002705 <b>คำสั่งซื้ออนุมัติแล้ว</b>\n"
        f"📃 เลขที่คำสั่งซื้อ: <code>{order.order_no}</code>\n"
        f"📦 แพ็กเกจ: {package.name if package else 'N/A'}\n"
        f"💰 ราคา: {order.price if hasattr(order, 'price') else 'N/A'}\n"
        f"👤 ยูสเซอร์: {mask_username(player.username if player else 'N/A')}"
    )

    if TELEGRAM_BOT_TOKEN and CHANNEL_PAYMENT:
        try:
            await send_message(CHANNEL_PAYMENT, caption)
        except Exception as e:
            print("⚠️ ไม่สามารถส่งข้อความไป Telegram:", e)

    return JSONResponse({"status": "success", "message": "อนุมัติคำสั่งซื้อเรียบร้อยแล้ว"})

# ------------------------
# Approve via Telegram callback
# ------------------------
@router.post("/api/telegram/callback")
async def telegram_callback(request: Request):
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

    player_row = await database.fetch_one(select(players.c.id).where(players.c.username == user))
    if not player_row:
        return {"ok": False}

    order = await database.fetch_one(
        select(package_orders).where(
            (package_orders.c.status == "pending") &
            (package_orders.c.player_id == player_row.id) &
            (package_orders.c.slip_url != None)
        )
    )

    if order:
        await database.execute(
            package_orders.update().where(package_orders.c.id == order.id)
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
