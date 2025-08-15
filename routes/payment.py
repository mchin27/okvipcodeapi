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

load_dotenv()

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_PAYMENT = os.getenv("CHANNEL_PAYMENT")
CHANNEL_CODE = os.getenv("CHANNEL_CODE")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def mask_username(username: str) -> str:
    """ซ่อน username บางส่วน"""
    if len(username) <= 5:
        return username
    return username[:3] + '*' * (len(username) - 5) + username[-2:]


async def send_photo(chat_id: str, caption: str, file_path: str, buttons: list = None):
    """ส่งรูปภาพไป Telegram จากไฟล์ path"""
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
    """ส่งข้อความไป Telegram"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        response.raise_for_status()


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

    # สร้างชื่อไฟล์สุ่ม
    file_ext = os.path.splitext(slip.filename)[1]
    saved_filename = f"{uuid.uuid4()}{file_ext}"
    saved_filepath = os.path.join(upload_folder, saved_filename)

    # บันทึกไฟล์ลงดิสก์
    with open(saved_filepath, "wb") as buffer:
        shutil.copyfileobj(slip.file, buffer)

    # ข้อความหลักสำหรับ Telegram
    caption_main = (
        f"\U0001F9FE มีผู้ส่งสลิปชำระเงิน\n"
        f"\U0001F4E6 แพ็กเกจ: {package}\n"
        f"\U0001F4B0 ราคา: {price} บาท\n"
        f"🌐 ไซต์: {site}\n"
        f"\U0001F464 ยูสเซอร์: {user}"
    )
    caption_status = (
        f"⏳ สถานะรอตรวจสอบรายการสมัคร\n"
        f"📦 แพ็กเกจ: {package}\n"
        f"💰 ราคา: {price} บาท\n"
        f"🌐 ไซต์: {site}\n"
        f"👤 ยูสเซอร์: {mask_username(user)}"
    )

    # ส่งไป Telegram channel
    try:
        if TELEGRAM_BOT_TOKEN and CHANNEL_PAYMENT:
            buttons = [{
                "text": "✅ อนุมัติแพ็กเกจ",
                "callback_data": f"approve|{user}|{package}|{price}|{site}"
            }]
            await send_photo(CHANNEL_PAYMENT, caption_main, saved_filepath, buttons)

        if TELEGRAM_BOT_TOKEN and CHANNEL_CODE:
            await send_message(CHANNEL_CODE, caption_status)
    except Exception as e:
        print("⚠️ ไม่สามารถส่งข้อมูลไปยัง Telegram channel:", e)

    # ส่งไป Telegram user ถ้าขอแจ้งเตือน
    if notifyTelegram and telegramId:
        try:
            await send_photo(telegramId, caption_main, saved_filepath)
        except Exception as e:
            print("⚠️ ไม่สามารถส่งข้อมูลไปยัง Telegram user:", e)

    # ตรวจสอบ site ด้วย mapping
    site_map = {
        "jun88": "thai_jun88k36",
        "789bet": "thai_789bet",
        # เพิ่ม site อื่น ๆ ได้ตรงนี้
    }
    site = site_map.get(site, site)

    site_result = await database.fetch_one(
        select(sites.c.id).where(sites.c.site_key == site)
    )
    if not site_result:
        return JSONResponse({"status": "error", "message": f"ไม่พบไซต์ {site}"})
    site_id = site_result.id
    
    # ตรวจสอบ player โดยกรอง site_id ด้วย
    player_result = await database.fetch_one(
        select(players.c.id).where(
            (players.c.username == user) &
            (players.c.site_id == site_id)
        )
    )

    if not player_result:
        new_player_id = await database.execute(
            players.insert().values(
                username=user,
                site_id=site_id,
                created_at=datetime.utcnow()
            )
        )
    else:
        new_player_id = player_result.id

    # ตรวจสอบ package
    package_result = await database.fetch_one(select(packages.c.id).where(packages.c.name == package))
    if not package_result:
        return JSONResponse({"status": "error", "message": "ไม่พบแพ็กเกจ"})

    # บันทึกคำสั่งซื้อ
    await database.execute(package_orders.insert().values(
        player_id=new_player_id,
        package_id=package_result.id,
        slip_url=saved_filepath,  # path ไฟล์ slip
        notify_telegram=notifyTelegram,
        telegram_id=telegramId,
        status="pending"
    ))

    return JSONResponse({"status": "success", "message": "ข้อมูลถูกส่งเรียบร้อยแล้ว"})

