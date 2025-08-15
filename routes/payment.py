# routes/payment.py
import os
import httpx
import json
import shutil
import uuid
from fastapi import APIRouter, UploadFile, Form, File
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from db.database import database
from sqlalchemy import select
from datetime import datetime
from db.models import sites, players, packages, package_orders
import random
import string

load_dotenv()

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_PAYMENT = os.getenv("CHANNEL_PAYMENT")
CHANNEL_CODE = os.getenv("CHANNEL_CODE")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def mask_username(username: str) -> str:
    if len(username) <= 5:
        return username
    return username[:3] + '*' * (len(username) - 5) + username[-2:]


async def send_photo(chat_id: str, caption: str, file_path: str, buttons: list = None):
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    with open(file_path, "rb") as f:
        content = f.read()
    files = {"photo": (os.path.basename(file_path), content, "image/jpeg")}
    data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
    if buttons:
        data["reply_markup"] = json.dumps({
            "inline_keyboard": [[
                {"text": b["text"], "callback_data": b["callback_data"][:64]} for b in buttons
            ]]
        })
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, files=files)
        response.raise_for_status()


async def send_message(chat_id: str, message: str):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        response.raise_for_status()


def generate_order_no(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


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
    # สร้างโฟลเดอร์เก็บ slip
    upload_folder = "./uploads/slip"
    os.makedirs(upload_folder, exist_ok=True)

    # บันทึกไฟล์
    file_ext = os.path.splitext(slip.filename)[1]
    saved_filename = f"{uuid.uuid4()}{file_ext}"
    saved_filepath = os.path.join(upload_folder, saved_filename)
    with open(saved_filepath, "wb") as buffer:
        shutil.copyfileobj(slip.file, buffer)

    # สร้าง order_no
    order_no = generate_order_no()

    # ข้อความ Telegram สำหรับแอดมิน/ช่องทางหลัก
    caption_main = (
        f"\U0001F4E6 <b>คำสั่งซื้อใหม่</b>\n"
        f"\U0001F3C3 เลขที่คำสั่งซื้อ: <code>{order_no}</code>\n"
        f"\U0001F4E6 แพ็กเกจ: {package}\n"
        f"\U0001F4B0 ราคา: {price} บาท\n"
        f"🌐 ไซต์: {site}\n"
        f"\U0001F464 ยูสเซอร์: {user}"
    )

    # ข้อความ Telegram สำหรับ channel แจ้งสถานะ
    caption_status = (
        f"⏳ <b>สถานะรอตรวจสอบ</b>\n"
        f"📃 เลขที่คำสั่งซื้อ: <code>{order_no}</code>\n"
        f"📦 แพ็กเกจ: {package}\n"
        f"💰 ราคา: {price} บาท\n"
        f"🌐 ไซต์: {site}\n"
        f"👤 ยูสเซอร์: {mask_username(user)}"
    )

    # ส่ง Telegram
    try:
        if TELEGRAM_BOT_TOKEN and CHANNEL_PAYMENT:
            callback_data = f"approve|{user}|{package}|{price}|{site}"
            if len(callback_data) > 64:
                callback_data = callback_data[:64]
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

    # ตรวจสอบ site
    site_map = {"jun88": "thai_jun88k36", "789bet": "thai_789bet"}
    site = site_map.get(site, site)
    site_result = await database.fetch_one(
        select(sites.c.id).where(sites.c.site_key == site)
    )
    if not site_result:
        return JSONResponse({"status": "error", "message": f"ไม่พบไซต์ {site}"})
    site_id = site_result.id

    # ตรวจสอบ player
    player_result = await database.fetch_one(
        select(players.c.id).where(
            (players.c.username == user) & (players.c.site_id == site_id)
        )
    )
    if not player_result:
        new_player_id = await database.execute(
            players.insert().values(username=user, site_id=site_id)
        )
    else:
        new_player_id = player_result.id

    # ตรวจสอบ package
    package_result = await database.fetch_one(select(packages.c.id).where(packages.c.name == package))
    if not package_result:
        return JSONResponse({"status": "error", "message": "ไม่พบแพ็กเกจ"})

    # บันทึกคำสั่งซื้อ
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


@router.post("/api/approve-order")
async def approve_order(order_no: str = Form(...)):
    """อนุมัติคำสั่งซื้อด้วย order_no"""
    order = await database.fetch_one(
        select(package_orders).where(package_orders.c.order_no == order_no)
    )
    if not order:
        return JSONResponse({"status": "error", "message": "ไม่พบคำสั่งซื้อ"})

    await database.execute(
        package_orders.update()
        .where(package_orders.c.order_no == order_no)
        .values(status="approved", approved_time=datetime.utcnow())
    )

    # ดึงข้อมูล player และ package
    player = await database.fetch_one(
        select(players.c.username).where(players.c.id == order.player_id)
    )
    package = await database.fetch_one(
        select(packages.c.name).where(packages.c.id == order.package_id)
    )

    caption = (
        f"\U00002705 <b>คำสั่งซื้ออนุมัติแล้ว</b>\n"
        f"📃 เลขที่คำสั่งซื้อ: <code>{order.order_no}</code>\n"
        f"📦 แพ็กเกจ: {package.name if package else 'N/A'}\n"
        f"💰 ราคา: {order.price if hasattr(order,'price') else 'N/A'}\n"
        f"👤 ยูสเซอร์: {mask_username(player.username if player else 'N/A')}"
    )

    if TELEGRAM_BOT_TOKEN and CHANNEL_PAYMENT:
        try:
            await send_message(CHANNEL_PAYMENT, caption)
        except Exception as e:
            print("⚠️ ไม่สามารถส่งข้อความไป Telegram:", e)

    return JSONResponse({"status": "success", "message": "อนุมัติคำสั่งซื้อเรียบร้อยแล้ว"})
