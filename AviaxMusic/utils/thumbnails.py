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

def crop_center_circle(img, output_size, border, border_color, crop_scale=1.5):
    half_the_width = img.size[0] / 2
    half_the_height = img.size[1] / 2
    larger_size = int(output_size * crop_scale)
    img = img.crop(
        (
            half_the_width - larger_size/2,
            half_the_height - larger_size/2,
            half_the_width + larger_size/2,
            half_the_height + larger_size/2
        )
    )
    
    # Resize the image slightly smaller to accommodate white border
    inner_size = output_size - 2*border - 8  # 8 pixels for white border
    img = img.resize((inner_size, inner_size))
    
    # Create final image with transparent background
    final_img = Image.new("RGBA", (output_size, output_size), (0, 0, 0, 0))
    
    # Create white border circle
    white_border = Image.new("RGBA", (output_size - 2*border, output_size - 2*border), (255, 255, 255, 255))
    white_mask = Image.new("L", (output_size - 2*border, output_size - 2*border), 0)
    white_draw = ImageDraw.Draw(white_mask)
    white_draw.ellipse((0, 0, output_size - 2*border, output_size - 2*border), fill=255)
    
    # Create inner circle mask for main image
    mask_main = Image.new("L", (inner_size, inner_size), 0)
    draw_main = ImageDraw.Draw(mask_main)
    draw_main.ellipse((0, 0, inner_size, inner_size), fill=255)
    
    # Create outer border mask
    mask_border = Image.new("L", (output_size, output_size), 0)
    draw_border = ImageDraw.Draw(mask_border)
    draw_border.ellipse((0, 0, output_size, output_size), fill=255)
    
    # Paste white border
    final_img.paste(white_border, (border, border), white_mask)
    
    # Paste main image with slight offset for white border
    final_img.paste(img, (border + 4, border + 4), mask_main)
    
    # Apply final circular mask
    result = Image.composite(final_img, Image.new("RGBA", final_img.size, (0, 0, 0, 0)), mask_border)
    
    return result

def draw_text_with_shadow(background, draw, position, text, font, fill, shadow_offset=(3, 3), shadow_blur=5):
    
    shadow = Image.new('RGBA', background.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    
    shadow_draw.text(position, text, font=font, fill="black")
    
    
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    
    
    background.paste(shadow, shadow_offset, shadow)
    
    
    draw.text(position, text, font=font, fill=fill)

def add_green_boundary(image, border_width=3, border_color=(0, 255, 0, 255)):
    """Add a green boundary line to the image with a glow effect"""
    width, height = image.size
    new_width = width + 2 * border_width
    new_height = height + 2 * border_width
    
    # Create a new image with green border
    new_image = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    
    # Add glow effect
    glow = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rectangle([(0, 0), (new_width, new_height)], outline=border_color, width=border_width)
    
    # Apply blur to create glow
    glow = glow.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Paste the original image
    new_image.paste(image, (border_width, border_width))
    
    # Composite with glow
    new_image = Image.alpha_composite(new_image, glow)
    
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
        cache_path = f"cache/{videoid}_v4.png"
        if os.path.isfile(cache_path):
            return cache_path

        # Check memory cache
        if videoid in processed_cache:
            return processed_cache[videoid]

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

        # Process image
        youtube = Image.open(f"cache/thumb{videoid}.png")
        image1 = youtube.resize(changeImageSize(1280, 720, youtube.size))
        background = image1.convert("RGBA")
        
        # Create circular thumbnail with white border
        circle_thumbnail = crop_center_circle(youtube, 400, 20, (0, 255, 0, 180))
        circle_thumbnail = circle_thumbnail.resize((400, 400))
        circle_position = (120, 160)
        
        # Apply optimized effects
        background = enhance_thumbnail(background)
        background = background.filter(ImageFilter.BoxBlur(10))
        background = ImageEnhance.Brightness(background).enhance(0.6)
        
        # Generate and blend gradient
        gradient_colors = (random_color(), random_color())
        gradient = generate_gradient(1280, 720, *gradient_colors)
        background = Image.blend(background, gradient, 0.2)
        
        # Add green boundary with glow
        border_color = (0, 255, 0, 180)
        border_width = 5
        
        # Create a new image with border
        bordered_bg = Image.new("RGBA", (1280 + 2*border_width, 720 + 2*border_width), (0, 0, 0, 0))
        
        # Create glow effect
        glow = Image.new("RGBA", bordered_bg.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.rectangle(
            [(0, 0), (bordered_bg.width, bordered_bg.height)],
            outline=border_color,
            width=border_width
        )
        
        # Apply blur to create glow
        glow = glow.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Paste the background
        bordered_bg.paste(background, (border_width, border_width))
        
        # Composite with glow
        background = Image.alpha_composite(bordered_bg, glow)
        
        # Paste circular thumbnail with white border
        background.paste(circle_thumbnail, circle_position, circle_thumbnail)
        
        # Draw text and elements
        draw = ImageDraw.Draw(background)
        fonts = {
            'title': ImageFont.truetype("AviaxMusic/assets/font3.ttf", 45),
            'arial': ImageFont.truetype("AviaxMusic/assets/font2.ttf", 30),
            'normal': ImageFont.truetype("AviaxMusic/assets/font.ttf", 30)
        }

        # Add text
        title_parts = truncate(title)
        text_positions = [
            (565, 180, title_parts[0], fonts['title'], COLORS['white']),
            (565, 230, title_parts[1], fonts['title'], COLORS['white']),
            (565, 320, f"{channel}  |  {views[:23]}", fonts['arial'], COLORS['white'])
        ]

        for x, y, text, font, color in text_positions:
            draw.text((x+2, y+2), text, font=font, fill=COLORS['black'])  # Shadow
            draw.text((x, y), text, font=font, fill=color)

        # Add progress line
        if duration != "Live":
            line_start = 565
            line_length = 580
            progress = random.uniform(0.15, 0.85)
            
            # Draw progress line
            draw.line(
                [(line_start, 380), (line_start + line_length * progress, 380)],
                fill=COLORS['green'],
                width=4
            )
            draw.line(
                [(line_start + line_length * progress, 380), (line_start + line_length, 380)],
                fill=(200, 200, 200, 180),
                width=4
            )
            
            # Add duration
            draw.text((line_start, 400), duration, font=fonts['arial'], fill=COLORS['white'])

        # Save and cache
        background = background.convert("RGB")
        background.save(cache_path, optimize=True, quality=95)
        
        # Update memory cache
        processed_cache[videoid] = cache_path
        if len(processed_cache) > CACHE_SIZE:
            processed_cache.pop(next(iter(processed_cache)))
        
        return cache_path

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
