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

def render_label(link_name: str, qr_content: str, bar_color: str, dpi: int, font_pt: float) -> Image.Image:
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

    # Text limits in bar
    max_text_w = (bar_x1 - bar_x0) - int(0.18 * W)
    max_text_h = (bar_y1 - bar_y0) - int(0.15 * bar_h)

    start_px = pt_to_px(font_pt, dpi)
    font = fit_text(draw, link_name, max_text_w, max_text_h, start_px=start_px)

    # Perfect center
    cx = (bar_x0 + bar_x1) // 2
    cy = (bar_y0 + bar_y1) // 2
    draw.text((cx, cy), link_name, font=font, fill="black", anchor="mm")

    return img.convert("RGB")

# -----------------------------
# Streamlit UI (Form + Preview inside "tables"/cards)
# -----------------------------
st.set_page_config(page_title="EAI Links Label Generator", layout="wide")

st.markdown(
    """
    <style>
      .card {
        border: 1px solid #e6e6e6;
        border-radius: 14px;
        padding: 18px 18px 14px 18px;
        background: #ffffff;
      }
      .card h3 {
        margin-top: 0px;
        margin-bottom: 14px;
      }
      .center-title {
        text-align: center;
        margin-top: 0.2rem;
        margin-bottom: 1.2rem;
      }
      .btn-row {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-top: 14px;
      }
      /* Remove weird empty input-like box sometimes shown by markdown */
      .stMarkdown > div:empty { display:none; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h2 class='center-title'>EAI Links Label Generator</h2>", unsafe_allow_html=True)

COLOR_OPTIONS = {"🟥 Red": "#E43F6F", "🟦 Blue": "#008DD5"}

# Session state
if "label_img" not in st.session_state:
    st.session_state.label_img = None
if "download_name" not in st.session_state:
    st.session_state.download_name = "label.png"
if "dpi" not in st.session_state:
    st.session_state.dpi = 300

left, right = st.columns([1, 1.25], gap="large")

# -------- Left card: Form --------
with left:
    st.markdown("<div class='card'><h3>Form</h3>", unsafe_allow_html=True)

    link_name = st.text_input("Link", value="2L3")
    qr_content = st.text_input("QR Content", value="2L3/D12-43/AE12-43/48P")

    st.markdown("**Color**")
    choice = st.radio("", list(COLOR_OPTIONS.keys()), horizontal=True, label_visibility="collapsed")
    bar_color = COLOR_OPTIONS[choice]

    dpi = st.selectbox("DPI", [300, 200, 150], index=0)
    font_pt = st.selectbox("Font size", [8, 9, 10, 11, 12], index=2)

    # Generate button at bottom of the form card
    if st.button("Generate", type="primary", use_container_width=True):
        img = render_label(
            link_name.strip(),
            qr_content.strip(),
            bar_color,
            dpi=int(dpi),
            font_pt=float(font_pt),
        )
        st.session_state.label_img = img
        st.session_state.download_name = f"{(link_name.strip() or 'label')}.png"
        st.session_state.dpi = int(dpi)

    st.markdown("</div>", unsafe_allow_html=True)

# -------- Right card: Preview --------
with right:
    st.markdown("<div class='card'><h3>Preview</h3>", unsafe_allow_html=True)

    if st.session_state.label_img is None:
        st.info("Click Generate to show the preview.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.image(st.session_state.label_img)

        # Centered download button at bottom of preview card
        buf = io.BytesIO()
        st.session_state.label_img.save(buf, format="PNG", dpi=(st.session_state.dpi, st.session_state.dpi))

        st.markdown("<div class='btn-row'>", unsafe_allow_html=True)
        st.download_button(
            "Download PNG",
            data=buf.getvalue(),
            file_name=st.session_state.download_name,
            mime="image/png",
        )
        st.markdown("</div></div>", unsafe_allow_html=True)
