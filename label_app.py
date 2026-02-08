import io
import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Optional

# ==========================================
# 1. CONFIGURATION & DESIGN TOKENS
# ==========================================
class Design:
    # Colors
    RED = "#F43F5E"     # Modern Rose/Red
    BLUE = "#0EA5E9"    # Professional Sky Blue
    DARK = "#1E293B"    # Slate Dark
    WHITE = "#FFFFFF"
    GRAY_LIGHT = "#F8FAFC"
    
    # Label Dimensions (cm)
    COPPER_W, COPPER_H = 2.5, 3.5
    FIBER_W, FIBER_H = 5.0, 3.5
    
    # Branding
    APP_TITLE = "LinkLabel Pro"
    PRIMARY_BTN = "#4F46E5" # Indigo

# ==========================================
# 2. UTILITIES & GEOMETRY
# ==========================================
def cm_to_px(cm: float, dpi: int) -> int:
    return int(round((cm / 2.54) * dpi))

def pt_to_px(pt: float, dpi: int) -> int:
    return int(round((pt * dpi) / 72.0))

def get_font(size_px: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Enhanced font loader with better fallbacks."""
    paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size=max(8, int(size_px)))
        except:
            continue
    return ImageFont.load_default()

def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, start_pt: float, dpi: int) -> ImageFont.FreeTypeFont:
    size = pt_to_px(start_pt, dpi)
    while size >= 10:
        font = get_font(size, bold=True)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_w and (bbox[3] - bbox[1]) <= max_h:
            return font
        size -= 1
    return get_font(10, bold=True)

def generate_qr(data: str, size_px: int) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=Design.DARK, back_color="white").convert("RGBA")
    return img.resize((size_px, size_px), resample=Image.Resampling.LANCZOS)

# ==========================================
# 3. CORE RENDERERS
# ==========================================
def render_copper(link: str, qr_data: str, color: str, dpi: int, font_pt: float) -> Image.Image:
    W, H = cm_to_px(Design.COPPER_W, dpi), cm_to_px(Design.COPPER_H, dpi)
    img = Image.new("RGBA", (W, H), Design.WHITE)
    draw = ImageDraw.Draw(img)
    
    padding = int(0.08 * W)
    
    # 1. QR Code (Top)
    qr_size = W - (2 * padding)
    qr_img = generate_qr(qr_data, qr_size)
    img.alpha_composite(qr_img, (padding, padding))
    
    # 2. Pill (Bottom)
    pill_h = int(0.22 * H)
    pill_w = W - (2 * padding)
    y_start = H - pill_h - padding
    
    draw.rounded_rectangle(
        [(padding, y_start), (W - padding, H - padding)], 
        radius=pill_h // 2, 
        fill=color
    )
    
    # 3. Text
    font = fit_text(draw, link, pill_w * 0.85, pill_h * 0.7, font_pt, dpi)
    draw.text((W // 2, y_start + pill_h // 2), link, font=font, fill=Design.WHITE, anchor="mm")
    
    return img.convert("RGB")

def render_fiber(qr_data: str, items: List[Tuple[str, str]], dpi: int, font_pt: float) -> Image.Image:
    W, H = cm_to_px(Design.FIBER_W, dpi), cm_to_px(Design.FIBER_H, dpi)
    img = Image.new("RGBA", (W, H), Design.WHITE)
    draw = ImageDraw.Draw(img)
    
    padding = int(0.05 * H)
    gap = int(0.03 * H)
    
    # 1. QR Code (Left)
    qr_side = H - (2 * padding)
    qr_img = generate_qr(qr_data, qr_side)
    img.alpha_composite(qr_img, (padding, padding))
    
    # 2. Pill Column (Right)
    panel_x0 = qr_side + (2 * padding)
    panel_w = W - panel_x0 - padding
    
    # Logic: Always space as if there are 6 slots for consistency
    max_slots = 6
    slot_h = (H - (2 * padding) - (max_slots - 1) * gap) // max_slots
    
    total_items = len(items)
    # Center the stack if fewer than 6 items
    stack_h = (total_items * slot_h) + ((total_items - 1) * gap)
    current_y = (H - stack_h) // 2
    
    for text, color in items:
        draw.rounded_rectangle(
            [(panel_x0, current_y), (panel_x0 + panel_w, current_y + slot_h)],
            radius=slot_h // 2,
            fill=color
        )
        
        font = fit_text(draw, text, panel_w * 0.85, slot_h * 0.7, font_pt, dpi)
        draw.text((panel_x0 + panel_w // 2, current_y + slot_h // 2), text, font=font, fill=Design.WHITE, anchor="mm")
        current_y += slot_h + gap
        
    return img.convert("RGB")

# ==========================================
# 4. STREAMLIT UI
# ==========================================
st.set_page_config(page_title=Design.APP_TITLE, layout="wide", page_icon="🏷️")

# Custom Professional CSS
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    
    .main {{ background-color: #F1F5F9; }}
    
    .stApp {{
        background: #f8fafc;
    }}
    
    /* Card Styling */
    .st-emotion-cache-12w0qpk {{
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e2e8f0;
    }}
    
    h1 {{
        color: {Design.DARK};
        font-weight: 800 !important;
        letter-spacing: -0.05rem;
    }}
    
    .stButton>button {{
        background-color: {Design.PRIMARY_BTN} !important;
        color: white !important;
        border-radius: 0.5rem !important;
        border: none !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
    }}

    .preview-box {{
        background: #e2e8f0;
        padding: 20px;
        border-radius: 12px;
        display: flex;
        justify-content: center;
        border: 2px dashed #cbd5e1;
    }}
    </style>
""", unsafe_allow_html=True)

def main():
    st.title(f"🏷️ {Design.APP_TITLE}")
    st.markdown("Generate high-resolution professional network equipment labels.")
    
    col_form, col_pre = st.columns([1, 1], gap="large")
    
    with col_form:
        st.subheader("Configuration")
        
        with st.container(border=True):
            l_type = st.selectbox("Label Template", ["Copper (2.5x3.5cm)", "Fiber 1 Unit (5x3.5cm)", "Fiber 2 Unit (5x3.5cm)"])
            
            c1, c2 = st.columns(2)
            dpi = c1.select_slider("Print Quality (DPI)", options=[150, 200, 300, 600], value=300)
            f_size = c2.number_input("Base Font Size (pt)", min_value=6, max_value=16, value=10)
            
            qr_text = st.text_area("QR Code Metadata", value="SN: EAI-2024-001\nREV: 2.0\nLOC: DC-A1", height=100)

            # Contextual Inputs
            items_to_render = []
            if "Copper" in l_type:
                link = st.text_input("Link Identifier", value="2L3")
                c_pick = st.radio("Label Color", ["Red", "Blue"], horizontal=True)
                target_color = Design.RED if c_pick == "Red" else Design.BLUE
            else:
                n = 3 if "1 Unit" in l_type else 6
                st.write("Link Identifiers & Colors")
                for i in range(n):
                    r1, r2 = st.columns([3, 1])
                    t = r1.text_input(f"ID {i+1}", f"LINK-{i+1}", key=f"t{i}")
                    c = r2.selectbox(f"Color {i+1}", ["Red", "Blue"], key=f"c{i}", label_visibility="collapsed")
                    items_to_render.append((t, Design.RED if c == "Red" else Design.BLUE))

            generate = st.button("Generate Label", use_container_width=True)

    with col_pre:
        st.subheader("Live Preview")
        if generate:
            with st.spinner("Rendering..."):
                if "Copper" in l_type:
                    final_img = render_copper(link, qr_text, target_color, dpi, f_size)
                    fname = f"label_{link}.png"
                else:
                    final_img = render_fiber(qr_text, items_to_render, dpi, f_size)
                    fname = "label_fiber.png"
                
                # Center the preview image using a container style
                st.markdown('<div class="preview-box">', unsafe_allow_html=True)
                st.image(final_img, use_container_width=False)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Download
                buf = io.BytesIO()
                final_img.save(buf, format="PNG", dpi=(dpi, dpi))
                st.download_button(
                    label="💾 Download Print-Ready PNG",
                    data=buf.getvalue(),
                    file_name=fname,
                    mime="image/png",
                    use_container_width=True
                )
        else:
            st.info("Configure the parameters and click 'Generate' to see the preview.")

if __name__ == "__main__":
    main()
