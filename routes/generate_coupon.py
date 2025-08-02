import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter

router = APIRouter()

TEMPLATE_PATH = "image/template_coupon.png"
FONT_PATH = "fonts/Anuphan-Bold.ttf"
FONT_SIZE_CODE = 34  # จาก 32 → 42

SAVE_DIR = "generated_coupons"
BASE_URL = "/static/generated_coupons"
os.makedirs(SAVE_DIR, exist_ok=True)

class CouponRequest(BaseModel):
    code: str
    user: str

@router.post("/generate-coupon")
def generate_coupon(data: CouponRequest, request: Request):
    try:
        background = Image.open(TEMPLATE_PATH).convert("RGBA")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template not found: {e}")

    CODE = data.code.strip()
    USER = data.user.strip()

    # Generate barcode
    barcode_class = barcode.get_barcode_class("code128")
    barcode_image = barcode_class(CODE, writer=ImageWriter())

    barcode_buffer = BytesIO()
    barcode_image.write(barcode_buffer, {
        "module_height": 14.0,   # จาก 10 → 20 (ความสูงของแถบบาร์)
        "text_distance": 1,      # ระยะห่างข้อความกับบาร์
        "font_size": 12          # จาก 12 → 20 (ขนาดตัวเลขใต้บาร์โค้ด)
    })
    barcode_buffer.seek(0)
    barcode_img = Image.open(barcode_buffer).convert("RGBA")

    # Resize barcode to fit inside white box
    barcode_width, barcode_height = 520, 140  # จาก 420x90 → ใหญ่ขึ้น
    barcode_img = barcode_img.resize((barcode_width, barcode_height))

    draw = ImageDraw.Draw(background)

    try:
        font_code = ImageFont.truetype(FONT_PATH, FONT_SIZE_CODE)
    except IOError:
        raise HTTPException(status_code=500, detail="Font file not found or unreadable")

    # White box assumed area (based on template image)
    box_x, box_y, box_w, box_h = 110, 805, 500, 140

    # แปลง cm เป็น px (96 dpi)
    cm_to_px = 27.8
    shift_x = int(2 * cm_to_px)  # 12 ซม. ไปขวา = 454 px
    shift_y = int(3 * cm_to_px)  # 3 ซม. ขึ้น = -113 px

    # ปรับตำแหน่งบาร์โค้ด
    barcode_x = box_x + (box_w - barcode_width) // 2 + shift_x
    barcode_y = box_y + 5 + shift_y

    background.paste(barcode_img, (barcode_x, barcode_y), mask=barcode_img)

    # วาดข้อความโค้ดใต้บาร์โค้ด
    bbox = font_code.getbbox(CODE)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    text_x = box_x + (box_w - text_w) // 2 + shift_x
    text_y = barcode_y + barcode_height + 10
    draw.text((text_x, text_y), CODE, font=font_code, fill="black")

    # วาดข้อความ user ใต้ข้อความโค้ด
    bbox_user = font_code.getbbox(USER)
    user_w, user_h = bbox_user[2] - bbox_user[0], bbox_user[3] - bbox_user[1]
    user_x = box_x + (box_w - user_w) // 2 + shift_x
    user_y = text_y + text_h + 5
    draw.text((user_x, user_y), USER, font=font_code, fill="black")

    # Save file
    filename = f"coupon_{CODE}_{USER}.png".replace(" ", "_")
    save_path = os.path.join(SAVE_DIR, filename)
    background.save(save_path, format="PNG")

    coupon_url = request.base_url._url.rstrip("/") + BASE_URL + "/" + filename
    return JSONResponse({"url": coupon_url})
