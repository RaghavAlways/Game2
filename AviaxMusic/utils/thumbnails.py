# ATLEAST GIVE CREDITS IF YOU STEALING :(((((((((((((((((((((((((((((((((((((
# ELSE NO FURTHER PUBLIC THUMBNAIL UPDATES

import random
import logging
import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
import asyncio
from functools import lru_cache
import time

logging.basicConfig(level=logging.INFO)

# Cache for processed images
CACHE_SIZE = 100
processed_cache = {}

@lru_cache(maxsize=50)
def changeImageSize(maxWidth, maxHeight, image_size):
    widthRatio = maxWidth / image_size[0]
    heightRatio = maxHeight / image_size[1]
    newWidth = int(widthRatio * image_size[0])
    newHeight = int(heightRatio * image_size[1])
    return (newWidth, newHeight)

def truncate(text):
    if not text:
        return ["", ""]
    words = text.split()
    text1 = []
    text2 = []
    len1 = 0
    
    for word in words:
        word_len = len(word) + 1  # +1 for space
        if len1 + word_len < 30:
            text1.append(word)
            len1 += word_len
        else:
            text2.append(word)
            
    return [" ".join(text1), " ".join(text2)]

# Predefine common colors
COLORS = {
    'transparent': (0, 0, 0, 0),
    'black': (0, 0, 0, 255),
    'white': (255, 255, 255, 255),
    'green': (0, 255, 0, 180)
}

@lru_cache(maxsize=20)
def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def generate_gradient(width, height, start_color, end_color):
    base = Image.new('RGBA', (width, height), start_color)
    top = Image.new('RGBA', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = [int(60 * (y / height)) for y in range(height) for x in range(width)]
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def add_border(image, border_width, border_color):
    width, height = image.size
    new_width = width + 2 * border_width
    new_height = height + 2 * border_width
    new_image = Image.new("RGBA", (new_width, new_height), border_color)
    new_image.paste(image, (border_width, border_width))
    return new_image

def crop_center_circle(img, output_size, border_width=10):
    """Create a circular thumbnail with enhanced white border and glow effect"""
    # Convert and resize image
    img = img.convert("RGBA")
    
    # Calculate sizes
    total_size = output_size
    inner_size = output_size - (border_width * 2)
    
    # Create mask for outer white circle with glow
    mask_outer = Image.new('L', (total_size, total_size), 0)
    mask_draw = ImageDraw.Draw(mask_outer)
    
    # Draw multiple circles for enhanced glow effect
    for i in range(4):
        mask_draw.ellipse(
            (i, i, total_size - i, total_size - i),
            fill=255 - (i * 30)
        )
    
    # Create mask for inner circle
    mask_inner = Image.new('L', (inner_size, inner_size), 0)
    mask_draw_inner = ImageDraw.Draw(mask_inner)
    mask_draw_inner.ellipse((0, 0, inner_size, inner_size), fill=255)
    
    # Create output image with white background and glow
    output = Image.new('RGBA', (total_size, total_size), (255, 255, 255, 255))
    output = output.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Resize and crop input image
    img_resized = img.resize((inner_size, inner_size), Image.Resampling.LANCZOS)
    
    # Paste the resized image with inner mask
    output.paste(img_resized, (border_width, border_width), mask_inner)
    
    # Apply outer mask to get final circular shape
    output.putalpha(mask_outer)
    
    return output

def draw_text_with_shadow(background, draw, position, text, font, fill, shadow_offset=(3, 3), shadow_blur=5):
    
    shadow = Image.new('RGBA', background.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    
    shadow_draw.text(position, text, font=font, fill="black")
    
    
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    
    
    background.paste(shadow, shadow_offset, shadow)
    
    
    draw.text(position, text, font=font, fill=fill)

def add_green_boundary(image, border_width=6, border_color=(0, 255, 0, 255)):
    """Add an enhanced green boundary line to the image with multiple glow layers"""
    width, height = image.size
    new_width = width + 2 * border_width
    new_height = height + 2 * border_width
    
    # Create a new image with transparent background
    new_image = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    
    # Add multiple glow layers with increasing intensity
    for i in range(4):
        glow = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_color = (0, 255, 0, 255 - (i * 40))  # Brighter green glow
        glow_draw.rectangle(
            [(i, i), (new_width - i, new_height - i)],
            outline=glow_color,
            width=border_width - i
        )
        # Apply stronger blur for outer layers
        glow = glow.filter(ImageFilter.GaussianBlur(radius=2 + i))
        new_image = Image.alpha_composite(new_image, glow)
    
    # Add white border for extra visibility
    white_border = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    white_draw = ImageDraw.Draw(white_border)
    white_draw.rectangle(
        [(border_width//2, border_width//2),
         (new_width - border_width//2, new_height - border_width//2)],
        outline=(255, 255, 255, 200),
        width=3
    )
    new_image = Image.alpha_composite(new_image, white_border)
    
    # Paste the original image
    new_image.paste(image, (border_width, border_width))
    
    return new_image

def enhance_thumbnail(image):
    """Optimized thumbnail enhancement"""
    enhancers = [
        (ImageEnhance.Contrast, 1.2),
        (ImageEnhance.Sharpness, 1.2),
        (ImageEnhance.Brightness, 1.1)
    ]
    
    for enhancer_class, factor in enhancers:
        image = enhancer_class(image).enhance(factor)
    return image

async def gen_thumb(videoid: str):
    try:
        if os.path.isfile(f"cache/{videoid}_v4.png"):
            return f"cache/{videoid}_v4.png"
        
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]
        
        title = re.sub("\W+", " ", result.get("title", "Unsupported Title")).title()
        duration = result.get("duration", "Live")
        thumbnail = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        if not thumbnail:
            raise ValueError("No thumbnail URL found")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                    await f.write(await resp.read())
                    await f.close()

        # Process main background
        youtube = Image.open(f"cache/thumb{videoid}.png")
        image1 = youtube.resize((1280, 720), Image.Resampling.LANCZOS)
        background = image1.convert("RGBA")
        
        # Enhance background
        background = enhance_thumbnail(background)
        background = background.filter(ImageFilter.GaussianBlur(10))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        
        # Create circular thumbnail with enhanced white border
        circle_thumbnail = crop_center_circle(youtube, 400, border_width=10)
        circle_pos = (120, 160)
        
        # Add enhanced green border with glow
        bordered_bg = Image.new('RGBA', (1280 + 12, 720 + 12), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(bordered_bg)
        
        # Draw multiple glowing borders
        for offset in range(5):
            border_draw.rectangle(
                [(offset, offset), (1280 + 12 - offset, 720 + 12 - offset)],
                outline=(0, 255, 0, 200 - offset * 35),
                width=3
            )
        
        # Add white border for extra visibility
        border_draw.rectangle(
            [(2, 2), (1280 + 10, 720 + 10)],
            outline=(255, 255, 255, 200),
            width=2
        )
        
        # Paste background
        bordered_bg.paste(background, (6, 6))
        
        # Add glow effect to circular thumbnail
        glow_layer = Image.new('RGBA', bordered_bg.size, (0, 0, 0, 0))
        glow_layer.paste(circle_thumbnail, circle_pos, circle_thumbnail)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(3))
        bordered_bg = Image.alpha_composite(bordered_bg, glow_layer)
        
        # Paste circular thumbnail
        bordered_bg.paste(circle_thumbnail, circle_pos, circle_thumbnail)
        
        # Add text with enhanced visibility
        draw = ImageDraw.Draw(bordered_bg)
        font = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 40)
        font2 = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 70)
        
        # Draw title with shadow
        title1 = truncate(title)
        draw_text_with_shadow(bordered_bg, draw, (480, 180), title1[0], font2, 'white', shadow_offset=(3, 3), shadow_blur=7)
        if title1[1]:
            draw_text_with_shadow(bordered_bg, draw, (480, 280), title1[1], font2, 'white', shadow_offset=(3, 3), shadow_blur=7)
        
        # Draw duration with shadow
        if duration != "Live":
            draw_text_with_shadow(bordered_bg, draw, (480, 380), duration, font, 'white', shadow_offset=(2, 2), shadow_blur=5)
        
        bordered_bg = bordered_bg.convert("RGB")
        bordered_bg.save(f"cache/{videoid}_v4.png", optimize=True, quality=95)
        
        return f"cache/{videoid}_v4.png"
    except Exception as e:
        logging.error(f"Error generating thumbnail: {e}")
        return None

# Clean up old thumbnails periodically
async def cleanup_old_thumbnails():
    while True:
        try:
            current_time = time.time()
            cache_dir = "cache"
            for file in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, file)
                if os.path.isfile(file_path):
                    # Remove files older than 24 hours
                    if current_time - os.path.getctime(file_path) > 86400:
                        os.remove(file_path)
        except Exception as e:
            logging.error(f"Error in cleanup: {e}")
        await asyncio.sleep(3600)  # Run every hour
