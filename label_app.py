import io
import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# Label rendering utilities (2.5 cm x 3.5 cm, QR + colored bar)
# ============================================================
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
            continue
    return ImageFont.load_default()

def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, start_px: int) -> ImageFont.ImageFont:
    size = int(start_px)
    while size >= 8:
        font = load_font(size)
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        if (r - l) <= max_w and (b - t) <= max_h:
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
    # Fixed physical size (portrait)
    W = cm_to_px(2.5, dpi)
    H = cm_to_px(3.5, dpi)

    img = Image.new("RGBA", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # Layout ratios (kept close to your sample)
    pad_lr = int(0.07 * W)
    top_pad = int(0.06 * H)
    bottom_pad = int(0.06 * H)
    gap = int(0.04 * H)
    bar_h = int(0.22 * H)

    # QR zone
    qr_side = W - 2 * pad_lr
    qr_zone_y0 = top_pad
    qr_zone_y1 = H - bar_h - gap
    qr_target = min(qr_side, qr_zone_y1 - qr_zone_y0)

    qr_img = make_qr(qr_content, qr_target)
    qr_x = (W - qr_target) // 2
    qr_y = qr_zone_y0 + ((qr_zone_y1 - qr_zone_y0) - qr_target) // 2
    img.alpha_composite(qr_img, (qr_x, qr_y))

    # Bottom rounded bar
    bar_x0 = int(0.12 * W)
    bar_x1 = W - int(0.12 * W)
    bar_y0 = H - bar_h
    bar_y1 = H - bottom_pad
    radius = max(8, int(0.30 * bar_h))

    draw.rounded_rectangle([(bar_x0, bar_y0), (bar_x1, bar_y1)], radius=radius, fill=bar_color)

    # Text centered in bar
    max_text_w = (bar_x1 - bar_x0) - int(0.18 * W)
    max_text_h = (bar_y1 - bar_y0) - int(0.15 * bar_h)

    font = fit_text(draw, link_name, max_text_w, max_text_h, start_px=pt_to_px(font_pt, dpi))
    cx = (bar_x0 + bar_x1) // 2
    cy = (bar_y0 + bar_y1) // 2
    draw.text((cx, cy), link_name, font=font, fill="black", anchor="mm")

    return img.convert("RGB")

# ======================
# Streamlit UI (Modern)
# ======================
st.set_page_config(page_title="EAI Links Label Generator", layout="wide")

st.markdown(
    """
    <style>
      /* Page spacing */
      .block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; max-width: 1200px; }

      /* Title */
      .app-title {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0.2rem 0 1.2rem 0;
      }
      .app-subtitle {
        text-align: center;
        color: #6b7280;
        margin-top: -0.8rem;
        margin-bottom: 1.6rem;
        font-size: 14px;
      }

      /* Cards */
      .card {
        border: 1px solid rgba(229,231,235,1);
        background: rgba(255,255,255,1);
        border-radius: 16px;
        padding: 18px 18px 16px 18px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
      }
      .card h3 {
        margin: 0 0 12px 0;
        font-size: 18px;
        font-weight: 750;
      }

      /* Small helper text */
      .hint { color:#6b7280; font-size: 12px; margin-top:-6px; margin-bottom: 10px; }

      /* Download row */
      .dl-row { display:flex; justify-content:center; margin-top: 14px; }

      /* Make radio look tighter */
      div[role="radiogroup"] > label { margin-right: 16px; }

      /* Improve input widths */
      .stTextInput > div > div input { border-radius: 12px; }
      .stSelectbox > div > div { border-radius: 12px; }

      /* Buttons */
      .stButton > button, .stDownloadButton > button {
        border-radius: 12px !important;
        padding: 0.65rem 1rem !important;
        font-weight: 650 !important;
      }

      /* Make images centered inside preview */
      .stImage { display:flex; justify-content:center; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="app-title">EAI Links Label Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Generate a 2.5cm × 3.5cm QR label and export as PNG</div>', unsafe_allow_html=True)

COLOR_OPTIONS = {
    "🟥 Red": "#E43F6F",
    "🟦 Blue": "#008DD5",
}

# Session state
st.session_state.setdefault("label_img", None)
st.session_state.setdefault("download_name", "label.png")
st.session_state.setdefault("dpi", 300)

left, right = st.columns([1, 1.15], gap="large")

# -------- Form card --------
with left:
    st.markdown('<div class="card"><h3>Form</h3>', unsafe_allow_html=True)

    link_name = st.text_input("Link", value="2L3")
    qr_content = st.text_input("QR Content", value="2L3/D12-43/AE12-43/48P")

    st.markdown('<div class="hint">Tip: QR Content can be any string (e.g., 2L3/D12-43/AE12-43/48P).</div>', unsafe_allow_html=True)

    st.markdown("**Color**")
    choice = st.radio("", list(COLOR_OPTIONS.keys()), horizontal=True, label_visibility="collapsed")
    bar_color = COLOR_OPTIONS[choice]

    c1, c2 = st.columns(2)
    with c1:
        dpi = st.selectbox("DPI", [300, 200, 150], index=0)
    with c2:
        font_pt = st.selectbox("Font size", [8, 9, 10, 11, 12], index=2)

    generate = st.button("Generate", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------- Preview card --------
with right:
    st.markdown('<div class="card"><h3>Preview</h3>', unsafe_allow_html=True)

    if generate:
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

    if st.session_state.label_img is None:
        st.info("Fill the form and click Generate.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.image(st.session_state.label_img)

        buf = io.BytesIO()
        st.session_state.label_img.save(buf, format="PNG", dpi=(st.session_state.dpi, st.session_state.dpi))

        st.markdown('<div class="dl-row">', unsafe_allow_html=True)
        st.download_button(
            "Download PNG",
            data=buf.getvalue(),
            file_name=st.session_state.download_name,
            mime="image/png",
        )
        st.markdown("</div></div>", unsafe_allow_html=True)
