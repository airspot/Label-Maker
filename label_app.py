import io
import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont

# -----------------------------
# Size helpers (cm -> px)
# -----------------------------
def cm_to_px(cm: float, dpi: int) -> int:
    inches = cm / 2.54
    return int(round(inches * dpi))

def load_font(size: int) -> ImageFont.ImageFont:
    # Try common fonts; fallback to default
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            pass
    return ImageFont.load_default()

def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, start_size: int = 80):
    size = start_size
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

def make_qr(data: str, target_px: int) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Dark gray QR like your image
    img = qr.make_image(fill_color="#4a4a4a", back_color="white").convert("RGBA")

    # Resize to target
    img = img.resize((target_px, target_px), resample=Image.Resampling.NEAREST)
    return img

def render_label(liaison_name: str, qr_content: str, bar_color: str, dpi: int = 300) -> Image.Image:
    # Exact physical size requested: 2.5 cm x 3.5 cm (portrait)
    W = cm_to_px(2.5, dpi)
    H = cm_to_px(3.5, dpi)

    img = Image.new("RGBA", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # Proportions close to your example image
    pad = int(0.07 * W)                # side padding
    top_pad = int(0.06 * H)            # top padding
    bar_h = int(0.22 * H)              # bottom colored bar
    gap = int(0.04 * H)                # gap between QR and bar

    # QR square area
    qr_side = W - 2 * pad
    qr_y0 = top_pad
    qr_y1 = H - bar_h - gap

    # Make QR fit inside (center vertically in its zone)
    qr_target = min(qr_side, qr_y1 - qr_y0)
    qr_img = make_qr(qr_content, qr_target)
    qr_x = (W - qr_target) // 2
    qr_y = qr_y0 + ((qr_y1 - qr_y0) - qr_target) // 2
    img.alpha_composite(qr_img, (qr_x, qr_y))

    # Colored bar (simple, no border)
    bar_y0 = H - bar_h
    bar_x0 = int(0.12 * W)
    bar_x1 = W - int(0.12 * W)
    radius = max(8, int(0.12 * bar_h))  # slight rounding like your image

    draw.rounded_rectangle(
        [(bar_x0, bar_y0), (bar_x1, H - int(0.06 * H))],
        radius=radius,
        fill=bar_color,
        outline=None,
    )

    # Text centered in the bar
    text_area_w = (bar_x1 - bar_x0) - int(0.18 * W)
    text_area_h = bar_h - int(0.10 * H)
    font, (tw, th) = fit_text(draw, liaison_name, text_area_w, text_area_h, start_size=70)

    tx = bar_x0 + ((bar_x1 - bar_x0) - tw) // 2
    ty = bar_y0 + ((H - int(0.06 * H) - bar_y0) - th) // 2
    draw.text((tx, ty), liaison_name, font=font, fill="black")

    # Convert to RGB for clean PNG export
    return img.convert("RGB")

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Simple Liaison Label", layout="centered")
st.title("Simple Liaison Label Generator")

with st.form("label_form"):
    liaison_name = st.text_input("Liaison name (shown under QR)", value="2L3")
    qr_content = st.text_input("QR content (encoded inside QR)", value="2L3/D12-43/AE12-43/48P")

    # Color choices exactly as you asked
    color = st.radio(
        "Choose color",
        options=["#E43F6F", "#008DD5"],
        index=0,
        horizontal=True,
    )

    dpi = st.selectbox("Export DPI (keeps 2.5×3.5 cm size)", [300, 200, 150], index=0)
    submitted = st.form_submit_button("Generate")

if submitted:
    label_img = render_label(liaison_name.strip(), qr_content.strip(), color, dpi=dpi)

    st.subheader("Preview")
    st.image(label_img, use_container_width=False)

    buf = io.BytesIO()
    # Save with DPI metadata so printing keeps the physical size
    label_img.save(buf, format="PNG", dpi=(dpi, dpi))
    st.download_button(
        "Download PNG",
        data=buf.getvalue(),
        file_name=f"{liaison_name.strip() or 'label'}.png",
        mime="image/png",
    )

st.caption("Label size is fixed to 2.5 cm × 3.5 cm (portrait). No border. QR + colored name bar.")
