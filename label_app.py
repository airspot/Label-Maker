import io
import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple

# ==========================================
# 1. CONFIGURATION & DESIGN TOKENS
# ==========================================
class Design:
    RED = "#FF4B4B"      
    BLUE = "#42a5f5"     
    SOFT_GRAY = "#F1F5F9" 
    DARK_TEXT = "#000000"
    WHITE = "#FFFFFF"
    BTN_BG = "#1E293B" 
    
    # Label Sizes (cm)
    COPPER_W, COPPER_H = 2.5, 3.5
    FIBER_W, FIBER_H = 5.0, 3.5
    
    APP_TITLE = "Finatech Labeling Tool"

# ==========================================
# 2. CORE RENDERING ENGINE
# ==========================================
def cm_to_px(cm: float, dpi: int) -> int:
    return int(round((cm / 2.54) * dpi))

def pt_to_px(pt: float, dpi: int) -> int:
    return int(round((pt * dpi) / 72.0))

def get_font(size_px: int) -> ImageFont.FreeTypeFont:
    paths = ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"]
    for p in paths:
        try: return ImageFont.truetype(p, size=max(6, int(size_px)))
        except: continue
    return ImageFont.load_default()

def fit_text(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int, start_pt: float, dpi: int) -> ImageFont.FreeTypeFont:
    size = pt_to_px(start_pt, dpi)
    while size >= 6:
        font = get_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_w and (bbox[3] - bbox[1]) <= max_h:
            return font
        size -= 1
    return get_font(6)

def generate_qr(data: str, size_px: int) -> Image.Image:
    qr_data = data if data.strip() else " "
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E293B", back_color="white").convert("RGBA")
    return img.resize((size_px, size_px), resample=Image.Resampling.LANCZOS)

def render_copper_multi(qr_data: str, items: List[Tuple[str, str]], dpi: int, font_pt: float) -> Image.Image:
    """Renders Copper labels with multiple pill-shaped IDs (2 for 24P, 4 for 48P)"""
    W, H = cm_to_px(Design.COPPER_W, dpi), cm_to_px(Design.COPPER_H, dpi)
    img = Image.new("RGBA", (W, H), Design.WHITE)
    draw = ImageDraw.Draw(img)
    
    padding = int(0.08 * W)
    qr_size = W - (2 * padding)
    img.alpha_composite(generate_qr(qr_data, qr_size), (padding, padding))
    
    # Calculate layout for pills
    y_start_area = qr_size + (2 * padding)
    available_h = H - y_start_area - padding
    num_items = len(items)
    gap = int(0.02 * H)
    pill_h = (available_h - (num_items - 1) * gap) // num_items
    
    current_y = y_start_area
    for text, color in items:
        fill_color = color if text.strip() else Design.SOFT_GRAY
        draw.rounded_rectangle([(padding, current_y), (W - padding, current_y + pill_h)], radius=pill_h // 2, fill=fill_color)
        
        if text.strip():
            font = fit_text(draw, text, (W - 2*padding) * 0.85, pill_h * 0.7, font_pt, dpi)
            draw.text((W // 2, current_y + pill_h // 2), text, font=font, fill=Design.DARK_TEXT, anchor="mm")
        current_y += pill_h + gap
        
    return img.convert("RGB")

def render_fiber(qr_data: str, items: List[Tuple[str, str]], dpi: int, font_pt: float) -> Image.Image:
    W, H = cm_to_px(Design.FIBER_W, dpi), cm_to_px(Design.FIBER_H, dpi)
    img = Image.new("RGBA", (W, H), Design.WHITE)
    draw = ImageDraw.Draw(img)
    padding, gap = int(0.06 * H), int(0.03 * H)
    qr_side = H - (2 * padding)
    img.alpha_composite(generate_qr(qr_data, qr_side), (padding, padding))
    
    panel_x0 = qr_side + (2 * padding)
    panel_w = W - panel_x0 - padding
    max_slots = 6
    slot_h = (H - (2 * padding) - (max_slots - 1) * gap) // max_slots
    stack_h = (len(items) * slot_h) + ((len(items) - 1) * gap)
    current_y = (H - stack_h) // 2
    
    for text, color in items:
        fill_color = color if text.strip() else Design.SOFT_GRAY
        draw.rounded_rectangle([(panel_x0, current_y), (panel_x0 + panel_w, current_y + slot_h)], radius=slot_h // 2, fill=fill_color)
        if text.strip():
            font = fit_text(draw, text, panel_w * 0.85, slot_h * 0.7, font_pt, dpi)
            draw.text((panel_x0 + panel_w // 2, current_y + slot_h // 2), text, font=font, fill=Design.DARK_TEXT, anchor="mm")
        current_y += slot_h + gap
    return img.convert("RGB")

# ==========================================
# 3. STREAMLIT INTERFACE
# ==========================================
st.set_page_config(page_title=Design.APP_TITLE, layout="wide")

# Custom CSS (Keeping your original styling)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F8FAFC; }}
    div[data-testid="stRadio"] div[role="radiogroup"] label:nth-of-type(1) p {{ color: {Design.RED} !important; font-weight: 600; }}
    div[data-testid="stRadio"] div[role="radiogroup"] label:nth-of-type(2) p {{ color: {Design.BLUE} !important; font-weight: 600; }}
    div.stButton > button {{ background-color: {Design.BTN_BG} !important; color: white !important; border: 1px solid {Design.BTN_BG} !important; }}
    </style>
""", unsafe_allow_html=True)

def main():
    st.title(f"🏷️ {Design.APP_TITLE}")
    
    col_form, col_pre = st.columns([1.1, 1], gap="large")
    
    with col_form:
        with st.container(border=True):
            st.subheader("Global Settings")
            l_type = st.selectbox("Patch Panel Type", ["Copper 24P", "Copper 48P", "Fiber 1 Unit", "Fiber 2 Unit"])
            
            c1, c2 = st.columns(2)
            dpi = c1.select_slider("Print Quality (DPI)", options=[150, 300, 600], value=300)
            f_size = c2.number_input("Font Size (Pt)", value=8) 
            qr_text = st.text_area("QR Code Metadata", value="", height=80)

            st.divider()
            st.subheader("Labeling Configuration")
            
            items_to_render = []
            
            # Logic for number of inputs based on selection
            if "Copper 24P" in l_type:
                n = 2
            elif "Copper 48P" in l_type:
                n = 4
            elif "Fiber 1 Unit" in l_type:
                n = 3
            else: # Fiber 2 Unit
                n = 6

            for i in range(n):
                r1, r2 = st.columns([2, 1])
                t = r1.text_input(f"ID {i+1}", value="", key=f"t{i}", label_visibility="collapsed", placeholder=f"ID {i+1}")
                c = r2.radio(f"Col {i+1}", ["Red", "Blue"], key=f"c{i}", horizontal=True, label_visibility="collapsed")
                items_to_render.append((t, Design.RED if c == "Red" else Design.BLUE))

            generate = st.button("Generate Label", use_container_width=True)

    with col_pre:
        st.subheader("Label Preview")
        if generate:
            if "Copper" in l_type:
                final_img = render_copper_multi(qr_text, items_to_render, dpi, f_size)
                fname = f"{l_type.lower().replace(' ', '_')}.png"
            else:
                final_img = render_fiber(qr_text, items_to_render, dpi, f_size)
                fname = f"{l_type.lower().replace(' ', '_')}.png"
            
            st.image(final_img, use_container_width=False)
            
            buf = io.BytesIO()
            final_img.save(buf, format="PNG", dpi=(dpi, dpi))
            st.download_button("Download PNG", buf.getvalue(), fname, "image/png", use_container_width=True)
        else:
            st.info("Click **Generate Label** to see the preview.")

if __name__ == "__main__":
    main()
