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
        
        # Process main background image
        youtube = Image.open(f"cache/thumb{videoid}.png")
        image_background = youtube.resize((1280, 720), Image.Resampling.LANCZOS)
        background = image_background.convert("RGBA")
        
        # Enhance background
        background = enhance_thumbnail(background)
        
        # Create a circular thumbnail for the top-left corner
        # Extract a square portion from the center of the image
        square_size = min(background.width, background.height)
        left = (background.width - square_size) // 2
        top = (background.height - square_size) // 2
        right = left + square_size
        bottom = top + square_size
        square_img = background.crop((left, top, right, bottom))
        
        # Create a circular mask
        circle_size = 300  # Size of the circular thumbnail
        circle_img = square_img.resize((circle_size, circle_size), Image.Resampling.LANCZOS)
        
        # Create the circular mask
        mask = Image.new('L', (circle_size, circle_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, circle_size, circle_size), fill=255)
        
        # Create the circular thumbnail with white border
        circle_border_size = 310  # Slightly larger for border
        circle_border = Image.new('RGBA', (circle_border_size, circle_border_size), (255, 255, 255, 0))
        circle_border_draw = ImageDraw.Draw(circle_border)
        circle_border_draw.ellipse((0, 0, circle_border_size-1, circle_border_size-1), outline=(255, 255, 255, 255), width=5)
        
        # Apply the circular mask to the image
        circle_output = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
        circle_output.paste(circle_img, (0, 0), mask)
        
        # Add a green glow around the circular thumbnail
        glow_size = circle_size + 20
        glow_img = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_img)
        
        # Draw multiple circles for a glowing effect
        for i in range(5):
            glow_draw.ellipse(
                (i, i, glow_size-i-1, glow_size-i-1),
                outline=(0, 255, 0, 200 - i * 40),
                width=2
            )
        
        # Apply blur to the glow
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Create the final background with border
        border_width = 12
        final_width = 1280 + border_width*2
        final_height = 720 + border_width*2
        final_img = Image.new('RGBA', (final_width, final_height), (0, 0, 0, 0))
        
        # Draw green border with glow
        border_draw = ImageDraw.Draw(final_img)
        for offset in range(6):
            border_draw.rectangle(
                [(offset, offset), (final_width - offset - 1, final_height - offset - 1)],
                outline=(0, 255, 0, 200 - offset * 30),
                width=3
            )
        
        # Add white border for extra visibility
        border_draw.rectangle(
            [(2, 2), (final_width - 3, final_height - 3)],
            outline=(255, 255, 255, 200),
            width=2
        )
        
        # Paste the main background image
        final_img.paste(background, (border_width, border_width))
        
        # Paste the glowing circle in the top-left corner
        paste_x = border_width + 30
        paste_y = border_width + 30
        final_img.paste(glow_img, (paste_x - 10, paste_y - 10), glow_img)
        
        # Paste the circular thumbnail
        final_img.paste(circle_output, (paste_x, paste_y), circle_output)
        
        # Paste the white border circle
        final_img.paste(circle_border, (paste_x - 5, paste_y - 5), circle_border)
        
        # Add text with enhanced visibility
        draw = ImageDraw.Draw(final_img)
        font_title = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 60)  # Smaller title font
        font_info = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 30)   # Smaller info font
        
        # Create a semi-transparent overlay for text background at the bottom
        overlay_height = 150
        overlay = Image.new('RGBA', (final_width, overlay_height), (0, 0, 0, 180))
        final_img.paste(overlay, (0, final_height - overlay_height), overlay)
        
        # Draw title with shadow - position it to the right of the circular thumbnail
        title1 = truncate(title)
        # First line of title - positioned at bottom of the image with better visibility
        draw_text_with_shadow(
            final_img, draw, 
            (border_width + 40, final_height - overlay_height + 20), 
            title1[0], font_title, 'white', 
            shadow_offset=(3, 3), shadow_blur=5
        )
        
        # Second line of title if it exists
        if title1[1]:
            draw_text_with_shadow(
                final_img, draw, 
                (border_width + 40, final_height - overlay_height + 90), 
                title1[1], font_title, 'white', 
                shadow_offset=(3, 3), shadow_blur=5
            )
        
        # Add duration info - position near the circular thumbnail
        draw_text_with_shadow(
            final_img, draw, 
            (paste_x + circle_size + 30, paste_y + 20), 
            f"Duration: {duration}", font_info, 'white', 
            shadow_offset=(2, 2), shadow_blur=2
        )
        
        # Add channel info 
        draw_text_with_shadow(
            final_img, draw, 
            (paste_x + circle_size + 30, paste_y + 60), 
            f"Channel: {channel}", font_info, 'white', 
            shadow_offset=(2, 2), shadow_blur=2
        )
        
        # Convert and save the final image
        final_img = final_img.convert("RGB")
        final_img.save(f"cache/{videoid}_v4.png")
        
        # Clean up temporary file
        try:
            os.remove(f"cache/thumb{videoid}.png")
        except:
            pass
            
        return f"cache/{videoid}_v4.png"
    except Exception as e:
        print(f"Error in thumbnail generation: {e}")
        # Use a default thumbnail if generation fails
        return "AviaxMusic/assets/thumbnail.png"

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
