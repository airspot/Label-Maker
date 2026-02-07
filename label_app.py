import io
import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont

# -----------------------------
# Size helpers (cm/pt -> px)
# -----------------------------
def cm_to_px(cm: float, dpi: int) -> int:
    return int(round((cm / 2.54) * dpi))

def pt_to_px(pt: float, dpi: int) -> int:
    # 1pt = 1/72 inch
    return int(round((pt * dpi) / 72.0))

def load_font(size_px: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=max(8, int(size_px)))
        except Exception:
            pass
    return ImageFont.load_default()

def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, start_px: int):
    size = int(start_px)
    while size >= 8:
        font = load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= max_w and h <= max_h:
            return font
        size -= 1
    return load_font(8)

def make_qr(data: str, target_px: int) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#4a4a4a", back_color="white").convert("RGBA")
    return img.resize((target_px, target_px), resample=Image.Resampling.NEAREST)

def render_label(liaison_name: str, qr_content: str, bar_color: str, dpi: int, font_pt: float) -> Image.Image:
    # Exact physical size: 2.5 cm x 3.5 cm (portrait)
    W = cm_to_px(2.5, dpi)
    H = cm_to_px(3.5, dpi)

    img = Image.new("RGBA", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # Proportions like your sample
    pad_lr = int(0.07 * W)
    top_pad = int(0.06 * H)
    bottom_pad = int(0.06 * H)
    gap = int(0.04 * H)
    bar_h = int(0.22 * H)

    # QR area
    qr_side = W - 2 * pad_lr
    qr_zone_y0 = top_pad
    qr_zone_y1 = H - bar_h - gap

    qr_target = min(qr_side, qr_zone_y1 - qr_zone_y0)
    qr_img = make_qr(qr_content, qr_target)

    qr_x = (W - qr_target) // 2
    qr_y = qr_zone_y0 + ((qr_zone_y1 - qr_zone_y0) - qr_target) // 2
    img.alpha_composite(qr_img, (qr_x, qr_y))

    # Bottom bar
    bar_x0 = int(0.12 * W)
    bar_x1 = W - int(0.12 * W)
    bar_y0 = H - bar_h
    bar_y1 = H - bottom_pad
    radius = max(8, int(0.30 * bar_h))

    draw.rounded_rectangle(
        [(bar_x0, bar_y0), (bar_x1, bar_y1)],
        radius=radius,
        fill=bar_color,
        outline=None,
    )

    # Text area limits inside bar
    max_text_w = (bar_x1 - bar_x0) - int(0.18 * W)
    max_text_h = (bar_y1 - bar_y0) - int(0.15 * bar_h)

    # Start size = chosen pt converted to px (keeps print size consistent)
    start_px = pt_to_px(font_pt, dpi)

    # Fit down if text is too long
    font = fit_text(draw, liaison_name, max_text_w, max_text_h, start_px=start_px)

    # Perfect center text
    cx = (bar_x0 + bar_x1) // 2
    cy = (bar_y0 + bar_y1) // 2
    draw.text((cx, cy), liaison_name, font=font, fill="black", anchor="mm")

    return img.convert("RGB")

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Simple Liaison Label", layout="centered")
st.title("Simple Liaison Label Generator")

COLOR_OPTIONS = {
    "🟪 Pink": "#E43F6F",
    "🟦 Blue": "#008DD5",
}

with st.form("label_form"):
    liaison_name = st.text_input("Liaison name (under QR)", value="2L3")
    qr_content = st.text_input("QR content", value="2L3/D12-43/AE12-43/48P")
