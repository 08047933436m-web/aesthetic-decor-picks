import os
import json
import io
import requests
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name, size, is_bold=False):
    """Loads clean Windows fonts (Segoe UI or Arial) for crisp typography."""
    windows_fonts = "C:/Windows/Fonts/"
    font_paths = []
    
    if font_name == "segoe":
        font_paths = [
            f"{windows_fonts}segoeuib.ttf" if is_bold else f"{windows_fonts}segoeui.ttf",
            f"{windows_fonts}arialbd.ttf" if is_bold else f"{windows_fonts}arial.ttf"
        ]
    else:
        font_paths = [
            f"{windows_fonts}arialbd.ttf" if is_bold else f"{windows_fonts}arial.ttf"
        ]
        
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    """Wraps text cleanly across multiple lines."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def create_pin(product, output_path):
    width, height = 1000, 1500
    pin = Image.new("RGB", (width, height), color=(249, 248, 246)) # Ivory background
    draw = ImageDraw.Draw(pin)

    # 1. Image loading
    img_height = 980
    img = None
    local_img_path = f"images/{product['id']}.jpg"
    
    if os.path.exists(local_img_path):
        try:
            img = Image.open(local_img_path).convert("RGB")
        except Exception as e:
            print(f"Local image read error {local_img_path}: {e}")

    if img is None:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(product["imageUrl"], headers=headers, timeout=5)
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception:
            pass

    if img:
        img_ratio = img.width / img.height
        target_ratio = width / img_height

        if img_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            left = (img.width - new_w) // 2
            img = img.crop((left, 0, left + new_w, img.height))
        else:
            new_h = int(img.width / target_ratio)
            top = (img.height - new_h) // 2
            img = img.crop((0, top, img.width, top + new_h))

        img = img.resize((width, img_height), Image.Resampling.LANCZOS)
        pin.paste(img, (0, 0))
    else:
        draw.rectangle([(0, 0), (width, img_height)], fill=(235, 233, 227))

    # 2. Modern Card Bottom Overlay
    card_top = 890
    card_shape = [(40, card_top), (width - 40, height - 50)]
    draw.rounded_rectangle(card_shape, radius=34, fill=(255, 255, 255))
    draw.rounded_rectangle(card_shape, radius=34, outline=(232, 229, 223), width=2)

    # 3. Badges
    tag_text = f"★ {product['tag'].upper()} • {product['category'].upper()}"
    font_badge = get_font("segoe", 23, is_bold=True)
    badge_x = 80
    badge_y = card_top + 45
    
    bbox = draw.textbbox((0, 0), tag_text, font=font_badge)
    badge_w = bbox[2] - bbox[0] + 30
    badge_h = bbox[3] - bbox[1] + 16
    draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)], radius=12, fill=(234, 239, 234))
    draw.text((badge_x + 15, badge_y + 8), tag_text, font=font_badge, fill=(79, 99, 82))

    # Discount badge
    discount_text = f"{product['discount']} OFF"
    font_disc = get_font("segoe", 23, is_bold=True)
    d_bbox = draw.textbbox((0, 0), discount_text, font=font_disc)
    d_w = d_bbox[2] - d_bbox[0] + 24
    d_x = width - 80 - d_w
    draw.rounded_rectangle([(d_x, badge_y), (d_x + d_w, badge_y + badge_h)], radius=12, fill=(200, 75, 71))
    draw.text((d_x + 12, badge_y + 8), discount_text, font=font_disc, fill=(255, 255, 255))

    # 4. Product Title
    font_title = get_font("segoe", 44, is_bold=True)
    lines = wrap_text(product["title"], font_title, width - 160, draw)
    title_y = badge_y + badge_h + 24
    for line in lines[:2]:
        draw.text((80, title_y), line, font=font_title, fill=(35, 34, 32))
        title_y += 56

    # 5. Price Section
    font_price = get_font("segoe", 52, is_bold=True)
    font_old = get_font("segoe", 32, is_bold=False)
    
    price_y = title_y + 16
    draw.text((80, price_y), product["price"], font=font_price, fill=(35, 34, 32))
    
    p_bbox = draw.textbbox((0, 0), product["price"], font=font_price)
    old_x = 80 + (p_bbox[2] - p_bbox[0]) + 18
    draw.text((old_x, price_y + 14), product["oldPrice"], font=font_old, fill=(160, 157, 152))
    old_bbox = draw.textbbox((old_x, price_y + 14), product["oldPrice"], font=font_old)
    draw.line([(old_x - 3, price_y + 30), (old_bbox[2] + 3, price_y + 30)], fill=(160, 157, 152), width=3)

    # 6. Call To Action Button
    cta_y = height - 150
    cta_shape = [(80, cta_y), (width - 80, cta_y + 68)]
    draw.rounded_rectangle(cta_shape, radius=18, fill=(79, 99, 82))
    
    cta_text = "CHECK DEALS & DETAILS ➔"
    font_cta = get_font("segoe", 26, is_bold=True)
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_cta)
    text_w = cta_bbox[2] - cta_bbox[0]
    draw.text(((width - text_w) // 2, cta_y + 20), cta_text, font=font_cta, fill=(255, 255, 255))

    pin.save(output_path, "JPEG", quality=92)
    print(f"Generated pin: {output_path}")

def main():
    os.makedirs("output_pins", exist_ok=True)
    with open("products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Generating English Pinterest pins for {len(products)} products...")
    for idx, product in enumerate(products, 1):
        filename = f"output_pins/pin_{idx}_{product['id']}.jpg"
        create_pin(product, filename)
    print("\nAll English pins successfully generated in output_pins/!")

if __name__ == "__main__":
    main()
