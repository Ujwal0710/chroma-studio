"""Generate a high-fidelity Scandinavian minimalist room image matching the Roomie Figma design."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def generate_roomie_sample_room(output_path: Path):
    width, height = 960, 720
    # Canvas
    img = Image.new("RGB", (width, height), (236, 234, 229)) # #ECEAE5
    draw = ImageDraw.Draw(img)

    # 1. Wall background with subtle lighting gradient (brighter near top-left window, softer toward bottom-right)
    arr = np.zeros((height, width, 3), dtype=np.float32)
    for y in range(height):
        for x in range(width):
            # Soft ambient gradient
            gradient = 0.94 + 0.08 * (1.0 - y / height) + 0.04 * (1.0 - x / width)
            arr[y, x, 0] = np.clip(235 * gradient, 0, 255)
            arr[y, x, 1] = np.clip(232 * gradient, 0, 255)
            arr[y, x, 2] = np.clip(227 * gradient, 0, 255)

    # 2. Seamless reflective light floor (bottom 35% of the frame)
    floor_y = int(height * 0.65)
    for y in range(floor_y, height):
        ratio = (y - floor_y) / float(height - floor_y)
        # Reflective soft white/bone floor with subtle forward gradient
        f_r = 246 - ratio * 14
        f_g = 244 - ratio * 14
        f_b = 240 - ratio * 12
        arr[y, :, 0] = f_r
        arr[y, :, 1] = f_g
        arr[y, :, 2] = f_b

    # Baseboard line
    arr[floor_y:floor_y+3, :, :] = [218, 215, 208]

    base_img = Image.fromarray(arr.astype(np.uint8))
    draw = ImageDraw.Draw(base_img)

    # 3. Soft Ambient Shadow on the floor
    # Shadow layer
    shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)

    # Shadow under sofa
    s_draw.ellipse([width * 0.45, height * 0.78, width * 0.95, height * 0.88], fill=(60, 50, 45, 60))
    # Shadow under table
    s_draw.ellipse([width * 0.28, height * 0.77, width * 0.48, height * 0.83], fill=(60, 50, 45, 75))
    # Shadow under lamp
    s_draw.ellipse([width * 0.10, height * 0.79, width * 0.28, height * 0.84], fill=(60, 50, 45, 70))
    # Shadow under plant
    s_draw.ellipse([width * 0.32, height * 0.62, width * 0.44, height * 0.68], fill=(60, 50, 45, 45))

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(14))
    base_img.paste(shadow_layer, (0, 0), shadow_layer)
    draw = ImageDraw.Draw(base_img)

    # 4. Scandinavian Heather Gray Fabric Sofa (on the right)
    sofa_x = int(width * 0.52)
    sofa_y = int(height * 0.44)
    sofa_w = int(width * 0.46)
    sofa_h = int(height * 0.36)

    # Sofa backrest
    draw.rounded_rectangle([sofa_x, sofa_y, sofa_x + sofa_w, sofa_y + int(sofa_h * 0.65)], radius=18, fill=(155, 158, 162), outline=(135, 138, 142), width=1)
    # Sofa seat cushion
    draw.rounded_rectangle([sofa_x - 15, sofa_y + int(sofa_h * 0.45), sofa_x + sofa_w, sofa_y + int(sofa_h * 0.85)], radius=14, fill=(175, 178, 182), outline=(145, 148, 152), width=1)
    # Sofa armrest
    draw.rounded_rectangle([sofa_x - 25, sofa_y + int(sofa_h * 0.35), sofa_x + 35, sofa_y + int(sofa_h * 0.85)], radius=12, fill=(162, 165, 169))
    # Throw pillow (Cream Alabaster linen)
    draw.rounded_rectangle([sofa_x + 25, sofa_y + int(sofa_h * 0.38), sofa_x + 95, sofa_y + int(sofa_h * 0.75)], radius=8, fill=(245, 242, 236), outline=(220, 216, 208), width=1)

    # Sofa wooden legs (Ash wood)
    leg_color = (195, 160, 125)
    draw.line([sofa_x + 10, sofa_y + int(sofa_h * 0.85), sofa_x - 5, sofa_y + sofa_h], fill=leg_color, width=6)
    draw.line([sofa_x + int(sofa_w * 0.4), sofa_y + int(sofa_h * 0.85), sofa_x + int(sofa_w * 0.4), sofa_y + sofa_h], fill=leg_color, width=6)
    draw.line([sofa_x + int(sofa_w * 0.85), sofa_y + int(sofa_h * 0.85), sofa_x + int(sofa_w * 0.88), sofa_y + sofa_h], fill=leg_color, width=6)

    # 5. Round White Scandinavian Side Table (center-left)
    table_cx = int(width * 0.38)
    table_cy = int(height * 0.64)
    table_rx = 70
    table_ry = 22

    # Table angled legs
    draw.line([table_cx - 45, table_cy + 15, table_cx - 65, table_cy + 115], fill=leg_color, width=5)
    draw.line([table_cx, table_cy + 18, table_cx, table_cy + 120], fill=leg_color, width=5)
    draw.line([table_cx + 45, table_cy + 15, table_cx + 65, table_cy + 115], fill=leg_color, width=5)

    # Table tabletop bevel
    draw.ellipse([table_cx - table_rx, table_cy - table_ry + 6, table_cx + table_rx, table_cy + table_ry + 6], fill=(225, 222, 216))
    # Table top (Crisp Matte White)
    draw.ellipse([table_cx - table_rx, table_cy - table_ry, table_cx + table_rx, table_cy + table_ry], fill=(252, 250, 246), outline=(230, 226, 220), width=1)

    # 6. Ceramic Planter & Green Potted Fern on Table
    pot_x = table_cx - 16
    pot_y = table_cy - 48
    draw.rounded_rectangle([pot_x, pot_y, pot_x + 32, pot_y + 36], radius=4, fill=(248, 246, 242), outline=(215, 210, 202), width=1)

    # Botanical fern leaves
    leaf_green_1 = (85, 115, 75)
    leaf_green_2 = (110, 140, 95)
    leaf_green_3 = (65, 95, 55)
    draw.arc([pot_x - 30, pot_y - 45, pot_x + 25, pot_y + 15], 180, 340, fill=leaf_green_1, width=3)
    draw.arc([pot_x + 5, pot_y - 55, pot_x + 60, pot_y + 15], 200, 360, fill=leaf_green_2, width=3)
    draw.arc([pot_x - 15, pot_y - 65, pot_x + 45, pot_y + 10], 190, 350, fill=leaf_green_3, width=3)
    draw.arc([pot_x - 40, pot_y - 30, pot_x + 10, pot_y + 20], 170, 320, fill=leaf_green_2, width=3)
    draw.arc([pot_x + 20, pot_y - 35, pot_x + 65, pot_y + 20], 210, 360, fill=leaf_green_1, width=3)

    # 7. Natural Ash Tripod Floor Lamp (on the far left)
    lamp_top_x = int(width * 0.18)
    lamp_top_y = int(height * 0.22)
    shade_w = 90
    shade_h = 75

    # Three slender wooden legs spreading down to floor
    draw.line([lamp_top_x, lamp_top_y + shade_h, lamp_top_x - 55, height * 0.82], fill=leg_color, width=4)
    draw.line([lamp_top_x, lamp_top_y + shade_h, lamp_top_x + 8, height * 0.81], fill=leg_color, width=4)
    draw.line([lamp_top_x, lamp_top_y + shade_h, lamp_top_x + 65, height * 0.83], fill=leg_color, width=4)

    # Black metal junction fixture
    draw.ellipse([lamp_top_x - 8, lamp_top_y + shade_h - 4, lamp_top_x + 8, lamp_top_y + shade_h + 8], fill=(35, 35, 35))

    # Linen Drum Shade (Oatmeal / Flax linen with warm inner illumination glow)
    # Inner glow
    shade_glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(shade_glow)
    g_draw.ellipse([lamp_top_x - shade_w, lamp_top_y - 20, lamp_top_x + shade_w, lamp_top_y + shade_h + 40], fill=(255, 245, 215, 45))
    shade_glow = shade_glow.filter(ImageFilter.GaussianBlur(18))
    base_img.paste(shade_glow, (0, 0), shade_glow)
    draw = ImageDraw.Draw(base_img)

    # Shade body
    draw.rounded_rectangle([lamp_top_x - int(shade_w/2), lamp_top_y, lamp_top_x + int(shade_w/2), lamp_top_y + shade_h], radius=4, fill=(244, 238, 226), outline=(215, 208, 195), width=1)
    # Subtle linen texture lines
    for ly in range(lamp_top_y + 6, lamp_top_y + shade_h - 4, 8):
        draw.line([lamp_top_x - int(shade_w/2) + 4, ly, lamp_top_x + int(shade_w/2) - 4, ly], fill=(230, 222, 208), width=1)

    # Ensure output directory exists and save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_img.save(output_path, "JPEG", quality=95)
    print(f"Sample room generated at: {output_path}")

if __name__ == "__main__":
    out = Path("f:/module/data/roomie_default_room.jpg")
    generate_roomie_sample_room(out)
