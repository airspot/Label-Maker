import io
import re
import qrcode
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# -----------------------------
# Helpers
# -----------------------------
def load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Tries common fonts; falls back to default PIL font if not found.
    """
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            continue
    return ImageFont.load_default()

def build_qr(data: str, box_size: int = 10, border: int = 2) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#4a4a4a", back_color="white").convert("RGBA")
    return img

def fit_text(draw: ImageDraw.ImageDraw, text: str, font_path_size_start: int, max_w: int, max_h: int):
    """
    Finds the largest font size that fits inside max_w x max_h.
    """
    size = font_path_size_start
    while size > 8:
        font = load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= max_w and h <= max_h:
            return font, (w, h)
        size -= 1
    font = load_font(10)
    bbox = draw.textbbox((0, 0), text, font=font)
    return font, (bbox[2] - bbox[0], bbox[3] - bbox[1])

def normalize_id(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", "", s)
    return s

def make_qr_payload(base_liaison: str, rack_dep: str, unit_dep: str, rack_arr: str, unit_arr: str, ports: str) -> str:
    base_liaison = normalize_id(base_liaison)
    rack_dep = normalize_id(rack_dep)
    unit_dep = normalize_id(unit_dep)
    rack_arr = normalize_id(rack_arr)
    unit_arr = normalize_id(unit_arr)
    ports = normalize_id(ports)

    # Format you used: 2L3/D12-43/AE12-43/48P
    return f"{base_liaison}/{rack_dep}-{unit_dep}/{rack_arr}-{unit_arr}/{ports}P"

def render_label(
    qr_payload: str,
    button_texts: list[str],
    canvas_w: int = 1400,
    canvas_h: int = 750,
    border_px: int = 6,
    bg_color: str = "white",
    border_color: str = "#1f1f1f",
    qr_side_px: int = 520,
    btn_color: str = "#ef2f68",
    text_color: str = "#111111",
) -> Image.Image:
    """
    Creates one label image with:
    - Left QR
    - Right stacked rounded rectangles with big text
    """
    img = Image.new("RGBA", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(img)

    # outer border
    draw.rectangle(
        [(border_px, border_px), (canvas_w - border_px, canvas_h - border_px)],
        outline=border_color,
        width=border_px,
    )

    # QR
    qr_img = build_qr(qr_payload, box_size=10, border=2)

    # Fit QR into qr_side_px square area (keep aspect)
    qr_img = qr_img.resize((qr_side_px, qr_side_px), resample=Image.Resampling.NEAREST)

    qr_x = int(canvas_w * 0.07)
    qr_y = (canvas_h - qr_side_px) // 2
    img.alpha_composite(qr_img, (qr_x, qr_y))

    # Buttons area
    right_x0 = int(canvas_w * 0.58)
    right_x1 = canvas_w - int(canvas_w * 0.07)

    # Choose spacing based on number of buttons
    n = max(1, len(button_texts))
    top_margin = int(canvas_h * 0.12)
    bottom_margin = int(canvas_h * 0.12)
    available_h = canvas_h - top_margin - bottom_margin

    gap = max(18, int(canvas_h * 0.03))
    btn_h = int((available_h - gap * (n - 1)) / n)
    btn_h = max(btn_h, 90)

    btn_radius = 35
    btn_w = right_x1 - right_x0

    for i, t in enumerate(button_texts):
        y0 = top_margin + i * (btn_h + gap)
        y1 = y0 + btn_h

        draw.rounded_rectangle(
            [(right_x0, y0), (right_x1, y1)],
            radius=btn_radius,
            fill=btn_color,
            outline=None,
        )

        # Fit text
        pad = 28
        max_w = btn_w - 2 * pad
        max_h = btn_h - 2 * pad
        font, (tw, th) = fit_text(draw, t, font_path_size_start=120, max_w=max_w, max_h=max_h)

        tx = right_x0 + (btn_w - tw) // 2
        ty = y0 + (btn_h - th) // 2
        draw.text((tx, ty), t, font=font, fill=text_color)

    return img.convert("RGB")

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Liaison Label Generator", layout="wide")
st.title("Liaison Label Generator (QR + Link Buttons)")

with st.sidebar:
    st.header("Style")
    canvas_w = st.number_input("Width (px)", 800, 4000, 1400, 50)
    canvas_h = st.number_input("Height (px)", 400, 3000, 750, 50)
    qr_side_px = st.number_input("QR size (px)", 200, 1200, 520, 10)
    btn_color = st.color_picker("Button color", "#ef2f68")
    border_color = st.color_picker("Border color", "#1f1f1f")
    border_px = st.number_input("Border thickness (px)", 1, 20, 6, 1)

st.subheader("Inputs (Form)")

c1, c2, c3 = st.columns(3)
with c1:
    base_liaison = st.text_input("Base liaison (example: 2L3)", value="2L3")
    ports = st.text_input("Nb ports (example: 48)", value="48")
with c2:
    rack_dep = st.text_input("Rack départ (example: D12)", value="D12")
    unit_dep = st.text_input("Unité départ (example: 43)", value="43")
with c3:
    rack_arr = st.text_input("Rack arrivée (example: AE12)", value="AE12")
    unit_arr = st.text_input("Unité arrivée (example: 43)", value="43")

st.markdown("### Links (buttons on the right)")
mode = st.radio("How to enter links?", ["Auto (2L3.1..N)", "Manual list"], horizontal=True)

if mode == "Auto (2L3.1..N)":
    n_links = st.number_input("How many links?", 1, 20, 4, 1)
    buttons = [f"{normalize_id(base_liaison)}.{i}" for i in range(1, int(n_links) + 1)]
else:
    links_text = st.text_area(
        "One per line (example:\n2L3.1\n2L3.2\n2L3.3\n2L3.4)",
        value="2L3.1\n2L3.2\n2L3.3\n2L3.4",
        height=150,
    )
    buttons = [line.strip() for line in links_text.splitlines() if line.strip()]

qr_payload = make_qr_payload(base_liaison, rack_dep, unit_dep, rack_arr, unit_arr, ports)
st.info(f"QR payload will be:\n\n{qr_payload}")

colA, colB = st.columns([1, 1])
with colA:
    generate = st.button("Generate label", type="primary")

if generate:
    label_img = render_label(
        qr_payload=qr_payload,
        button_texts=buttons,
        canvas_w=int(canvas_w),
        canvas_h=int(canvas_h),
        border_px=int(border_px),
        border_color=border_color,
        qr_side_px=int(qr_side_px),
        btn_color=btn_color,
    )

    st.subheader("Preview")
    st.image(label_img, use_container_width=True)

    # Download
    buf = io.BytesIO()
    label_img.save(buf, format="PNG")
    st.download_button(
        label="Download PNG",
        data=buf.getvalue(),
        file_name=f"{normalize_id(base_liaison)}_{normalize_id(rack_dep)}-{normalize_id(unit_dep)}__{normalize_id(rack_arr)}-{normalize_id(unit_arr)}__{normalize_id(ports)}P.png",
        mime="image/png",
    )
