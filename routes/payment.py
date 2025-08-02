import os
import httpx
import json
from fastapi import APIRouter, UploadFile, Form, File, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_PAYMENT = os.getenv("CHANNEL_PAYMENT")
CHANNEL_CODE = os.getenv("CHANNEL_CODE")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def mask_username(username: str) -> str:
    visible_length = 4
    if len(username) <= visible_length:
        return username
    masked_length = len(username) - visible_length
    return username[:visible_length] + '*' * masked_length

async def send_photo(chat_id: str, caption: str, slip: UploadFile, buttons: list = None):
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    content = await slip.read()
    slip.file.seek(0)

    files = {
        "photo": (slip.filename, content, slip.content_type)
    }

    data = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML"
    }

    if buttons:
        reply_markup = {
            "inline_keyboard": [[
                {"text": b["text"], "callback_data": b["callback_data"][:64]} for b in buttons
            ]]
        }
        data["reply_markup"] = json.dumps(reply_markup)

    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data, files=files)
        response.raise_for_status()

async def send_norti(chat_id: str, message: str):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        response.raise_for_status()

@router.post("/api/submit-slip")
async def submit_payment(
    package: str = Form(...),
    price: str = Form(...),
    site: str = Form(...),
    user: str = Form(...),
    slip: UploadFile = File(...),
    notifyTelegram: bool = Form(False),
    telegramId: str = Form(None)
):
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

    try:
        if TELEGRAM_BOT_TOKEN and CHANNEL_PAYMENT:
            buttons = [{"text": "✅ อนุมัติแพ็กเกจ", "callback_data": f"approve|{user}|{package}|{price}|{site}"}]
            await send_photo(CHANNEL_PAYMENT, caption_main, slip, buttons)
        if TELEGRAM_BOT_TOKEN and CHANNEL_CODE:
            await send_norti(CHANNEL_CODE, caption_status)
    except Exception as e:
        print("⚠️ ไม่สามารถส่งข้อมูลไปยัง Telegram channel:", e)

    if notifyTelegram and telegramId:
        try:
            await send_photo(telegramId, caption_main, slip)
        except Exception as e:
            print("⚠️ ไม่สามารถส่งข้อมูลไปยัง Telegram user:", e)

    return JSONResponse({"status": "success", "message": "ข้อมูลถูกส่งเรียบร้อยแล้ว"})

@router.post("/api/approve-payment")
async def approve_payment(request: Request):
    body = await request.json()
    callback_data = body.get("callback_data", "")

    if not callback_data.startswith("approve"):
        return JSONResponse({"status": "ignored"})

    try:
        _, user, package, price, site = callback_data.split("|")
        approved_message = (
            "✅ สมัครแพ็กเกจสำเร็จแล้ว!\n"
            f"📦 แพ็กเกจ: {package}\n"
            f"💰 ราคา: {price} บาท\n"
            f"🌐 ไซต์: {site}\n"
            f"👤 ยูสเซอร์: {mask_username(user)}\n"
            "ขอให้โชคดีในการยิงโค้ดครับ! หากมีปัญหาหรือข้อสงสัย ติดต่อแอดมินได้ตลอดเวลา 🙌"
        )
        await send_norti(CHANNEL_CODE, approved_message)
        return JSONResponse({"status": "approved"})
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)})

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()

    callback_query = body.get("callback_query")
    if not callback_query:
        return JSONResponse({"status": "ignored"})

    callback_data = callback_query.get("data", "")
    callback_id = callback_query.get("id")
    from_user = callback_query.get("from", {}).get("username", "ไม่ทราบชื่อ")

    print(f"[Webhook] Approving: {callback_data} from @{from_user}")

    if callback_data.startswith("approve"):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{BACKEND_API_URL}/api/approve-payment",
                    json={"callback_data": callback_data},
                    timeout=5.0
                )
                result = resp.json()

            answer_text = "✅ อนุมัติสำเร็จ" if result.get("status") == "approved" else "❌ เกิดข้อผิดพลาด"
        except Exception as e:
            answer_text = f"❌ ผิดพลาด: {str(e)}"
    else:
        answer_text = "⏳ กำลังดำเนินการ..."

    url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
    payload = {
        "callback_query_id": callback_id,
        "text": answer_text,
        "show_alert": False
    }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    except Exception as e:
        print("⚠️ ส่ง answerCallbackQuery ไม่สำเร็จ:", e)

    return JSONResponse({"status": "done"})
