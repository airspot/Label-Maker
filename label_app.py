import io
import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont

# =========================
# Design tokens / constants
# =========================
RED = "#E43F6F"
BLUE = "#008DD5"
QR_DARK = "#2f2f2f"
PRIMARY_BTN = "#ff4b4b"

# Fiber border look (like your image)
BORDER_COLOR = "#7a7a7a"
PILL_OUTLINE = "#3a3a3a"

# =========================
# Helpers: units, fonts, QR
# =========================
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
    # Higher capacity for multi-line content
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=QR_DARK, back_color="white").convert("RGBA")
    return img.resize((target_px, target_px), resample=Image.Resampling.NEAREST)

# =========================
# Layout helpers
# =========================
def pill_radius(h: int) -> int:
    return max(8, int(0.46 * h))

# =========================
# Renderers
# =========================
def render_copper_label(link_name: str, qr_content: str, bar_color: str, dpi: int, font_pt: float) -> Image.Image:
    # Copper: 2.5cm x 3.5cm (portrait), no border
    W = cm_to_px(2.5, dpi)
    H = cm_to_px(3.5, dpi)

    img = Image.new("RGBA", (W, H), "white")
    draw = ImageDraw.Draw(img)

    outer = int(0.06 * H)
    gap = int(0.045 * H)
    bar_h = int(0.22 * H)

    qr_zone_h = (H - 2 * outer) - gap - bar_h
    qr_side = min(W - 2 * outer, qr_zone_h)

    qr_img = make_qr(qr_content, qr_side)
    qr_x = outer + ((W - 2 * outer) - qr_side) // 2
    qr_y = outer + (qr_zone_h - qr_side) // 2
    img.alpha_composite(qr_img, (qr_x, qr_y))

    bar_x0 = int(0.12 * W)
    bar_x1 = W - int(0.12 * W)
    bar_y1 = H - outer
    bar_y0 = bar_y1 - bar_h
    draw.rounded_rectangle([(bar_x0, bar_y0), (bar_x1, bar_y1)], radius=pill_radius(bar_h), fill=bar_color)

    max_w = (bar_x1 - bar_x0) - int(0.18 * W)
    max_h = bar_h - int(0.25 * bar_h)
    font = fit_text(draw, link_name, max_w, max_h, start_px=pt_to_px(font_pt, dpi))
    draw.text(((bar_x0 + bar_x1) // 2, (bar_y0 + bar_y1) // 2), link_name, font=font, fill="black", anchor="mm")

    return img.convert("RGB")


def render_fiber_label(qr_content: str, items: list[tuple[str, str]], dpi: int, font_pt: float) -> Image.Image:
    """
    Fiber: 5.0cm x 3.5cm (landscape)
    ✅ Draw borders + alignment like your reference image:
      - Outer rounded border
      - Inner rounded border around the QR area
      - Pills with outline
      - Pills sizing based on 6-slot grid (so 1-unit doesn't look huge)
    """
    W = cm_to_px(5.0, dpi)
    H = cm_to_px(3.5, dpi)

    img = Image.new("RGBA", (W, H), "white")
    draw = ImageDraw.Draw(img)

    # Border thickness scales with DPI
    stroke = max(2, int(0.012 * H))       # outer border stroke
    inner_stroke = max(2, int(0.010 * H)) # QR frame stroke

    # Outer padding leaves room for outer border
    outer = int(0.06 * H)
    gap_main = int(0.045 * H)
    gap_rect = int(0.040 * H)

    # Outer rounded border (like the big border in your image)
    outer_radius = int(0.10 * H)
    draw.rounded_rectangle(
        [(stroke, stroke), (W - stroke, H - stroke)],
        radius=outer_radius,
        outline=BORDER_COLOR,
        width=stroke,
        fill="white",
    )

    # Content bounds inside outer border
    cx0 = outer + stroke
    cy0 = outer + stroke
    cx1 = W - outer - stroke
    cy1 = H - outer - stroke
    content_w = cx1 - cx0
    content_h = cy1 - cy0

    # QR area frame (second rounded border around QR)
    qr_frame_pad = int(0.015 * H)       # padding between frame and QR
    qr_frame_radius = int(0.09 * H)

    qr_side = content_h  # square as tall as usable height
    qr_frame_x0 = cx0
    qr_frame_y0 = cy0
    qr_frame_x1 = qr_frame_x0 + qr_side
    qr_frame_y1 = cy1

    # Draw QR frame
    draw.rounded_rectangle(
        [(qr_frame_x0, qr_frame_y0), (qr_frame_x1, qr_frame_y1)],
        radius=qr_frame_radius,
        outline=BORDER_COLOR,
        width=inner_stroke,
        fill="white",
    )

    # Place QR inside the frame with padding
    qr_target = qr_side - 2 * qr_frame_pad - inner_stroke
    qr_img = make_qr(qr_content, qr_target)
    qr_x = qr_frame_x0 + (qr_side - qr_target) // 2
    qr_y = qr_frame_y0 + (content_h - qr_target) // 2
    img.alpha_composite(qr_img, (qr_x, qr_y))

    # Right panel area (aligned like your image)
    right_x0 = qr_frame_x1 + gap_main
    right_x1 = cx1
    right_w = max(1, right_x1 - right_x0)

    # Slight inset so pills aren't touching right area edges
    inset = int(0.02 * W)
    right_x0 += inset
    right_x1 -= inset
    right_w = max(1, right_x1 - right_x0)

    n = max(1, len(items))

    # Reference sizing based on 6 slots (so 3-slot doesn't become huge)
    ref_slots = 6
    rect_h_ref = int((content_h - gap_rect * (ref_slots - 1)) / ref_slots)
    rect_h = max(rect_h_ref, int(0.12 * H))

    stack_h = n * rect_h + (n - 1) * gap_rect
    start_y = cy0 + max(0, (content_h - stack_h) // 2)

    for i, (txt, col) in enumerate(items):
        y0 = start_y + i * (rect_h + gap_rect)
        y1 = y0 + rect_h

        # Pill with outline (like your image)
        draw.rounded_rectangle(
            [(right_x0, y0), (right_x1, y1)],
            radius=pill_radius(rect_h),
            fill=col,
            outline=PILL_OUTLINE,
            width=max(2, int(0.006 * H)),
        )

        # Center text
        max_w = right_w - int(0.18 * right_w)
        max_h = rect_h - int(0.30 * rect_h)
        font = fit_text(draw, txt, max_w, max_h, start_px=pt_to_px(font_pt, dpi))
        draw.text(((right_x0 + right_x1) // 2, (y0 + y1) // 2), txt, font=font, fill="black", anchor="mm")

    return img.convert("RGB")


# =========================
# Streamlit UI (modern + adaptive)
# =========================
st.set_page_config(page_title="EAI Links Label Generator", layout="wide")

st.markdown(
    f"""
    <style>
      .block-container {{
        padding-top: 1.0rem;
        padding-bottom: 2.0rem;
        max-width: 1240px;
      }}
      .app-title {{
        text-align:center;
        font-size: 34px;
        font-weight: 850;
        letter-spacing: -0.6px;
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
        font-weight: 760;
      }}
      .stTextInput > div > div input {{ border-radius: 12px; }}
      .stTextArea textarea {{ border-radius: 12px !important; }}
      .stSelectbox > div > div {{ border-radius: 12px; }}

      /* Generate + Download same style */
      .stButton > button, .stDownloadButton > button {{
        background: {PRIMARY_BTN} !important;
        color: white !important;
        border: 1px solid {PRIMARY_BTN} !important;
        border-radius: 12px !important;
        padding: 0.70rem 1.05rem !important;
        font-weight: 720 !important;
      }}
      .stButton > button:hover, .stDownloadButton > button:hover {{
        filter: brightness(0.95);
      }}

      .btn-row {{
        display:flex;
        justify-content:center;
        margin-top: 14px;
      }}
      .stImage {{ display:flex; justify-content:center; }}
      div[role="radiogroup"] > label {{ margin-right: 16px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="app-title">EAI Links Label Generator</div>', unsafe_allow_html=True)

st.session_state.setdefault("label_img", None)
st.session_state.setdefault("download_name", "label.png")
st.session_state.setdefault("dpi", 300)

left, right = st.columns([1, 1.2], gap="large")

# ---------------- FORM ----------------
with left:
    st.markdown('<div class="card"><h3>Form</h3>', unsafe_allow_html=True)

    label_type = st.selectbox("Label type", ["Copper", "Fiber (1 unit)", "Fiber (2 unit)"], index=0)

    cA, cB = st.columns(2)
    with cA:
        dpi = st.selectbox("DPI", [300, 200, 150], index=0)
    with cB:
        font_pt = st.selectbox("Font size", [8, 9, 10, 11, 12], index=2)

    st.divider()

    # Multiline QR content (6+ lines)
    sample_qr = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6"
    qr_content = st.text_area("QR Content", value=sample_qr, height=140)

    if label_type == "Copper":
        link_name = st.text_input("Link", value="2L3")

        st.markdown("**Color**")
        color_choice = st.radio("", ["🟥 Red", "🟦 Blue"], horizontal=True, label_visibility="collapsed")
        bar_color = RED if "Red" in color_choice else BLUE

        if st.button("Generate", use_container_width=True):
            img = render_copper_label(link_name.strip(), qr_content, bar_color, int(dpi), float(font_pt))
            st.session_state.label_img = img
            st.session_state.download_name = f"{(link_name.strip() or 'label')}.png"
            st.session_state.dpi = int(dpi)

    else:
        n_boxes = 3 if label_type == "Fiber (1 unit)" else 6

        st.markdown("**Links**")
        if n_boxes == 6:
            default_texts = ["2L98.1", "2L98.2", "2L98.3", "2L98.4", "2L100.1", "2L100.2"]
            default_cols = [RED, RED, BLUE, BLUE, RED, RED]
        else:
            default_texts = ["2L98.1", "2L98.2", "2L98.3"]
            default_cols = [RED, RED, BLUE]

        items: list[tuple[str, str]] = []
        for i in range(n_boxes):
            r1, r2 = st.columns([2.2, 1.0])
            with r1:
                txt = st.text_input(f"Link {i+1}", value=default_texts[i])
            with r2:
                col_pick = st.radio(
                    f"c{i}",
                    ["🟥", "🟦"],
                    horizontal=True,
                    label_visibility="collapsed",
                    index=0 if default_cols[i] == RED else 1,
                    key=f"fiber_col_{i}",
                )
                col = RED if col_pick == "🟥" else BLUE
            items.append((txt.strip(), col))

        if st.button("Generate", use_container_width=True):
            img = render_fiber_label(qr_content=qr_content, items=items, dpi=int(dpi), font_pt=float(font_pt))
            st.session_state.label_img = img
            base = (items[0][0] if items and items[0][0] else "fiber_label")
            st.session_state.download_name = f"{base}.png"
            st.session_state.dpi = int(dpi)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- PREVIEW ----------------
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
