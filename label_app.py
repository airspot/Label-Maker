import io
import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple

# ==========================================
# 1. CONFIGURATION & DESIGN TOKENS
# ==========================================
class Design:
    RED = "#FF8095"      # High-contrast Soft Red
    BLUE = "#82D8FF"     # High-contrast Soft Blue
    DARK_TEXT = "#000000"
    WHITE = "#FFFFFF"
    
    COPPER_W, COPPER_H = 2.5, 3.5
    FIBER_W, FIBER_H = 5.0, 3.5
    
    APP_TITLE = "LinkLabel Pro"
    PRIMARY_BTN = "#FF4B4B"

# ==========================================
# 2. UTILITIES & GEOMETRY
# ==========================================
def cm_to_px(cm: float, dpi: int) -> int:
    return int(round((cm / 2.54) * dpi))

def pt_to_px(pt: float, dpi: int) -> int:
    return int(round((pt * dpi) / 72.0))

def get_font(size_px: int) -> ImageFont.FreeTypeFont:
    # Reliable font loading for different environments
    paths = ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"]
    for p in paths:
        try: return ImageFont.truetype(p, size=max(8, int(size_px)))
        except: continue
    return ImageFont.load_default()

def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, start_pt: float, dpi: int) -> ImageFont.FreeTypeFont:
    size = pt_to_px(start_pt, dpi)
    while size >= 8:
        font = get_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_w and (bbox[3] - bbox[1]) <= max_h:
            return font
        size -= 1
    return get_font(8)

def generate_qr(data: str, size_px: int) -> Image.Image:
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E293B", back_color="white").convert("RGBA")
    return img.resize((size_px, size_px), resample=Image.Resampling.LANCZOS)

# ==========================================
# 3. CORE RENDERERS
# ==========================================
def render_copper(link: str, qr_data: str, color: str, dpi: int, font_pt: float) -> Image.Image:
    W, H = cm_to_px(Design.COPPER_W, dpi), cm_to_px(Design.COPPER_H, dpi)
    img = Image.new("RGBA", (W, H), Design.WHITE)
    draw = ImageDraw.Draw(img)
    padding = int(0.08 * W)
    
    qr_size = W - (2 * padding)
    img.alpha_composite(generate_qr(qr_data, qr_size), (padding, padding))
    
    pill_h = int(0.22 * H)
    y_start = H - pill_h - padding
    draw.rounded_rectangle([(padding, y_start), (W - padding, H - padding)], radius=pill_h // 2, fill=color)
    
    font = fit_text(draw, link, (W - 2*padding) * 0.85, pill_h * 0.7, font_pt, dpi)
    draw.text((W // 2, y_start + pill_h // 2), link, font=font, fill=Design.DARK_TEXT, anchor="mm")
    return img.convert("RGB")

def render_fiber(qr_data: str, items: List[Tuple[str, str]], dpi: int, font_pt: float) -> Image.Image:
    W, H = cm_to_px(Design.FIBER_W, dpi), cm_to_px(Design.FIBER_H, dpi)
    img = Image.new("RGBA", (W, H), Design.WHITE)
    draw = ImageDraw.Draw(img)
    
    padding = int(0.06 * H)
    gap = int(0.03 * H)
    qr_side = H - (2 * padding)
    img.alpha_composite(generate_qr(qr_data, qr_side), (padding, padding))
    
    panel_x0 = qr_side + (2 * padding)
    panel_w = W - panel_x0 - padding
    max_slots = 6
    slot_h = (H - (2 * padding) - (max_slots - 1) * gap) // max_slots
    
    stack_h = (len(items) * slot_h) + ((len(items) - 1) * gap)
    current_y = (H - stack_h) // 2
    
    for text, color in items:
        draw.rounded_rectangle([(panel_x0, current_y), (panel_x0 + panel_w, current_y + slot_h)], radius=slot_h // 2, fill=color)
        font = fit_text(draw, text, panel_w * 0.85, slot_h * 0.7, font_pt, dpi)
        draw.text((panel_x0 + panel_w // 2, current_y + slot_h // 2), text, font=font, fill=Design.DARK_TEXT, anchor="mm")
        current_y += slot_h + gap
        
    return img.convert("RGB")

# ==========================================
# 4. STREAMLIT UI
# ==========================================
st.set_page_config(page_title=Design.APP_TITLE, layout="wide")

# Enhanced CSS for vertical alignment and framing
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F8FAFC; }}
    
    /* Center text and radio vertically in link rows */
    [data-testid="stHorizontalBlock"] {{
        align-items: center;
    }}

    /* Custom Preview Container Styling */
    .stElementContainer div[data-testid="stVerticalBlock"] > div:has(div.preview-container) {{
        background: #F1F5F9;
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        padding: 2rem;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 400px;
    }}
    
    .stButton > button {{
        background-color: {Design.PRIMARY_BTN} !important;
        border: none !important;
    }}
    </style>
""", unsafe_allow_html=True)

def main():
    st.title(f"🏷️ {Design.APP_TITLE}")
    
    col_form, col_pre = st.columns([1, 1], gap="large")
    
    with col_form:
        with st.container(border=True):
            st.subheader("Global Settings")
            l_type = st.selectbox("Label Type", ["Copper", "Fiber 1 Unit", "Fiber 2 Unit"])
            c1, c2 = st.columns(2)
            dpi = c1.select_slider("DPI", options=[150, 300, 600], value=300)
            f_size = c2.number_input("Font Pt", value=10)
            qr_text = st.text_area("QR Content", "LINK_ID: 001\nTYPE: EAI_OPTIC", height=80)

            st.divider()
            st.subheader("Link Configuration")
            
            items_to_render = []
            if "Copper" in l_type:
                r1, r2 = st.columns([2, 1])
                link = r1.text_input("Link ID", "2L3")
                c_choice = r2.radio("Color", ["Red", "Blue"], horizontal=True)
                target_color = Design.RED if c_choice == "Red" else Design.BLUE
            else:
                n = 3 if "1 Unit" in l_type else 6
                for i in range(n):
                    r1, r2 = st.columns([2, 1]) # Better spacing for text vs radios
                    t = r1.text_input(f"ID {i+1}", f"L{i+1}", key=f"t{i}", label_visibility="collapsed")
                    c = r2.radio(f"Col {i+1}", ["Red", "Blue"], key=f"c{i}", horizontal=True, label_visibility="collapsed")
                    items_to_render.append((t, Design.RED if c == "Red" else Design.BLUE))

            generate = st.button("Generate Label", use_container_width=True, type="primary")

    with col_pre:
        st.subheader("Label Preview")
        # We use a container to act as the visual frame
        preview_placeholder = st.container()
        
        with preview_placeholder:
            # Invisible marker for the CSS to target this specific container
            st.markdown('<div class="preview-container"></div>', unsafe_allow_html=True)
            
            if generate:
                if "Copper" in l_type:
                    final_img = render_copper(link, qr_text, target_color, dpi, f_size)
                    fname = f"copper_{link}.png"
                else:
                    final_img = render_fiber(qr_text, items_to_render, dpi, f_size)
                    fname = "fiber_label.png"
                
                # Image is now nested inside the preview_placeholder container
                st.image(final_img, use_container_width=False)
                
                buf = io.BytesIO()
                final_img.save(buf, format="PNG", dpi=(dpi, dpi))
                st.download_button("Download PNG", buf.getvalue(), fname, "image/png", use_container_width=True)
            else:
                st.write("Click **Generate Label** to see the preview here.")

if __name__ == "__main__":
    main()
