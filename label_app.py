import io
import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# Helpers: size + fonts
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
    img = qr.make_image(fill_color="#2f2f2f", back_color="white").convert("RGBA")
    return img.resize((target_px, target_px), resample=Image.Resampling.NEAREST)


# ============================================================
# Renderers
# ============================================================
def render_copper_label(link_name: str, qr_content: str, bar_color: str, dpi: int, font_pt: float) -> Image.Image:
    # Copper: 2.5 cm x 3.5 cm (portrait)
    W = cm_to_px(2.5, dpi)
    H = cm_to_px(3.5, dpi)

    img = Image.new("RGBA", (W, H), "white")
    draw = ImageDraw.Draw(img)

    pad_lr = int(0.07 * W)
    top_pad = int(0.06 * H)
    bottom_pad = int(0.06 * H)
    gap = int(0.04 * H)
    bar_h = int(0.22 * H)

    # QR
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

    draw.rounded_rectangle([(bar_x0, bar_y0), (bar_x1, bar_y1)], radius=radius, fill=bar_color)

    max_text_w = (bar_x1 - bar_x0) - int(0.18 * W)
    max_text_h = (bar_y1 - bar_y0) - int(0.15 * bar_h)

    font = fit_text(draw, link_name, max_text_w, max_text_h, start_px=pt_to_px(font_pt, dpi))
    cx = (bar_x0 + bar_x1) // 2
    cy = (bar_y0 + bar_y1) // 2
    draw.text((cx, cy), link_name, font=font, fill="black", anchor="mm")

    return img.convert("RGB")


def render_fiber_label(qr_content: str, items: list[tuple[str, str]], dpi: int, font_pt: float) -> Image.Image:
    """
    Fiber label: 5.0 cm x 3.5 cm (landscape), no border.
    Layout: QR on left + N rounded rectangles on right.
    items = [(text, color_hex), ...] where N is 3 (1 unit) or 6 (2 unit).
    """
    # Fiber: 5 cm x 3.5 cm (landscape)  ✅
    W = cm_to_px(5.0, dpi)
    H = cm_to_px(3.5, dpi)

    img = Image.new("RGBA", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # Overall padding
    pad = int(0.05 * H)
    gap_lr = int(0.04 * W)

    # Left QR block
    qr_side = int(H - 2 * pad)  # square as tall as usable height
    qr_x0 = pad
    qr_y0 = pad
    qr_img = make_qr(qr_content, qr_side)
    img.alpha_composite(qr_img, (qr_x0, qr_y0))

    # Right buttons area
    right_x0 = qr_x0 + qr_side + gap_lr
    right_x1 = W - pad
    right_w = max(1, right_x1 - right_x0)

    n = max(1, len(items))
    top = pad
    bottom = H - pad

    # Use nice gaps; auto-scale button height
    gap_y = max(8, int(0.03 * H))
    available_h = (bottom - top) - gap_y * (n - 1)
    btn_h = max(22, int(available_h / n))
    radius = max(10, int(0.45 * btn_h))

    for i, (txt, col) in enumerate(items):
        y0 = top + i * (btn_h + gap_y)
        y1 = y0 + btn_h

        # Rounded rect
        draw.rounded_rectangle([(right_x0, y0), (right_x1, y1)], radius=radius, fill=col)

        # Center text
        pad_text = int(0.10 * right_w)
        max_w = right_w - 2 * pad_text
        max_h = btn_h - int(0.25 * btn_h)

        font = fit_text(draw, txt, max_w, max_h, start_px=pt_to_px(font_pt, dpi))
        cx = (right_x0 + right_x1) // 2
        cy = (y0 + y1) // 2
        draw.text((cx, cy), txt, font=font, fill="black", anchor="mm")

    return img.convert("RGB")


# ============================================================
# Streamlit UI (Modern + Adaptive)
# ============================================================
st.set_page_config(page_title="EAI Links Label Generator", layout="wide")

PRIMARY_BTN = "#ff4b4b"

st.markdown(
    f"""
    <style>
      .block-container {{
        padding-top: 1.0rem;
        padding-bottom: 2.2rem;
        max-width: 1220px;
      }}

      .app-title {{
        text-align:center;
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0.2rem 0 1.1rem 0;
      }}

      .card {{
        border: 1px solid rgba(229,231,235,1);
        background: #ffffff;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
      }}
      .card h3 {{
        margin: 0 0 12px 0;
        font-size: 18px;
        font-weight: 750;
      }}

      .stTextInput > div > div input {{ border-radius: 12px; }}
      .stSelectbox > div > div {{ border-radius: 12px; }}

      .stButton > button, .stDownloadButton > button {{
        background: {PRIMARY_BTN} !important;
        color: white !important;
        border: 1px solid {PRIMARY_BTN} !important;
        border-radius: 12px !important;
        padding: 0.70rem 1.05rem !important;
        font-weight: 700 !important;
      }}
      .stButton > button:hover, .stDownloadButton > button:hover {{
        filter: brightness(0.95);
      }}

      .btn-row {{
        display:flex;
        justify-content:center;
        gap: 14px;
        margin-top: 14px;
      }}

      .stImage {{ display:flex; justify-content:center; }}

      /* Make radio tighter */
      div[role="radiogroup"] > label {{ margin-right: 16px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="app-title">EAI Links Label Generator</div>', unsafe_allow_html=True)

RED = "#E43F6F"
BLUE = "#008DD5"
COLOR_OPTIONS = {"🟥 Red": RED, "🟦 Blue": BLUE}

st.session_state.setdefault("label_img", None)
st.session_state.setdefault("download_name", "label.png")
st.session_state.setdefault("dpi", 300)

left, right = st.columns([1, 1.2], gap="large")

# -----------------------
# FORM
# -----------------------
with left:
    st.markdown('<div class="card"><h3>Form</h3>', unsafe_allow_html=True)

    label_type = st.selectbox(
        "Label type",
        ["Copper", "Fiber (1 unit)", "Fiber (2 unit)"],
        index=0,
    )

    dpi = st.selectbox("DPI", [300, 200, 150], index=0)
    font_pt = st.selectbox("Font size", [8, 9, 10, 11, 12], index=2)

    st.divider()

    if label_type == "Copper":
        link_name = st.text_input("Link", value="2L3")
        qr_content = st.text_input("QR Content", value="2L3/D12-43/AE12-43/48P")

        st.markdown("**Color**")
        choice = st.radio("", list(COLOR_OPTIONS.keys()), horizontal=True, label_visibility="collapsed")
        bar_color = COLOR_OPTIONS[choice]

        generate = st.button("Generate", use_container_width=True)

        if generate:
            img = render_copper_label(
                link_name.strip(),
                qr_content.strip(),
                bar_color,
                dpi=int(dpi),
                font_pt=float(font_pt),
            )
            st.session_state.label_img = img
            st.session_state.download_name = f"{(link_name.strip() or 'label')}.png"
            st.session_state.dpi = int(dpi)

    else:
        # Fiber: QR + multiple rectangles on the right
        qr_content = st.text_input("QR Content", value="FIBER/EXAMPLE/PAYLOAD")

        # Number of buttons depends on type
        n_boxes = 3 if label_type == "Fiber (1 unit)" else 6

        st.markdown("**Links (text + color)**")

        # Defaults matching your sample for 2-unit
        default_texts = (
            ["2L98.1", "2L98.2", "2L98.3", "2L98.4", "2L100.1", "2L100.2"]
            if n_boxes == 6
            else ["2L98.1", "2L98.2", "2L98.3"]
        )
        default_cols = (
            [RED, RED, BLUE, BLUE, RED, RED] if n_boxes == 6 else [RED, RED, BLUE]
        )

        items = []
        for i in range(n_boxes):
            cA, cB = st.columns([2.2, 1])
            with cA:
                t = st.text_input(f"Link {i+1}", value=default_texts[i])
            with cB:
                # Color choice per rectangle
                color_choice = st.radio(
                    f"Color {i+1}",
                    ["🟥", "🟦"],
                    horizontal=True,
                    label_visibility="collapsed",
                    index=0 if default_cols[i] == RED else 1,
                    key=f"fiber_color_{i}",
                )
                col = RED if color_choice == "🟥" else BLUE
            items.append((t.strip(), col))

        generate = st.button("Generate", use_container_width=True)

        if generate:
            img = render_fiber_label(
                qr_content=qr_content.strip(),
                items=items,
                dpi=int(dpi),
                font_pt=float(font_pt),
            )
            st.session_state.label_img = img
            # filename based on first link text if exists
            base_name = (items[0][0] if items and items[0][0] else "fiber_label")
            st.session_state.download_name = f"{base_name}.png"
            st.session_state.dpi = int(dpi)

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# PREVIEW
# -----------------------
with right:
    st.markdown('<div class="card"><h3>Preview</h3>', unsafe_allow_html=True)

    if st.session_state.label_img is None:
        st.info("Fill the form and click Generate.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.image(st.session_state.label_img)

        buf = io.BytesIO()
        st.session_state.label_img.save(buf, format="PNG", dpi=(st.session_state.dpi, st.session_state.dpi))

        st.markdown('<div class="btn-row">', unsafe_allow_html=True)
        st.download_button(
            "Download PNG",
            data=buf.getvalue(),
            file_name=st.session_state.download_name,
            mime="image/png",
        )
        st.markdown("</div></div>", unsafe_allow_html=True)
