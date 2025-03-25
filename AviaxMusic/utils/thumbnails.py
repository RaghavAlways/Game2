# ATLEAST GIVE CREDITS IF YOU STEALING :(((((((((((((((((((((((((((((((((((((
# ELSE NO FURTHER PUBLIC THUMBNAIL UPDATES

import random
import logging
import os
import re
import aiofiles
import aiohttp
import psutil
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
import asyncio
from functools import lru_cache
import time

logging.basicConfig(level=logging.INFO)

# Cache for processed images with timestamps for LRU implementation
CACHE_SIZE = 100
processed_cache = {}

@lru_cache(maxsize=50)
def changeImageSize(maxWidth, maxHeight, image_size):
    widthRatio = maxWidth / image_size[0]
    heightRatio = maxHeight / image_size[1]
    newWidth = int(widthRatio * image_size[0])
    newHeight = int(heightRatio * image_size[1])
    return (newWidth, newHeight)

@lru_cache(maxsize=50)
def get_text_dimensions(text, font):
    """Get the dimensions of a text with a specific font (cached for performance)"""
    # Create a dummy image to measure text size
    dummy_img = Image.new('RGB', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    return dummy_draw.textbbox((0, 0), text, font=font)[2:4]  # width, height

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
    # Get text dimensions for better positioning
    text_width, text_height = get_text_dimensions(text, font)
    
    shadow = Image.new('RGBA', background.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    
    shadow_draw.text(position, text, font=font, fill="black")
    
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    
    background.paste(shadow, shadow_offset, shadow)
    
    draw.text(position, text, font=font, fill=fill)
    
    return text_width, text_height

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
        # Check cache first to avoid reprocessing
        cache_path = f"cache/{videoid}_v5.png"
        if os.path.isfile(cache_path):
            # Update timestamp in cache for LRU implementation
            if videoid in processed_cache:
                processed_cache[videoid]["timestamp"] = time.time()
            return cache_path
            
        # Check if memory usage is too high
        if psutil.virtual_memory().percent > 85:
            await optimize_memory_usage()
        
        if videoid == "telegram":
            # Create simplified thumbnail for Telegram media
            image = Image.new("RGB", (1280, 720), (0, 0, 0))
            color = random_color()
            # Make a gradient background
            background = generate_gradient(1280, 720, (30, 30, 30), (color[0], color[1], color[2], 150))
            
            # Load a default icon
            icon_path = "assets/Telegram.png"
            if os.path.exists(icon_path):
                icon = Image.open(icon_path)
                # Make circular icon with enhanced border
                icon_size = 360  # Larger icon size for better visibility
                icon = crop_center_circle(icon, icon_size)
                # Center the icon (adjusted position to be higher up)
                background.paste(icon, (int((1280-icon_size)/2), int((720-icon_size)/2)-50), icon)
            
            # Add enhanced green boundary
            background = add_green_boundary(background)
            
            # Enhance the final thumbnail
            background = enhance_thumbnail(background)
            
            if not os.path.exists("cache"):
                os.makedirs("cache")
            
            # Save with optimization
            background.save(cache_path, format="PNG", optimize=True)
            
            # Add to cache dict for LRU tracking
            processed_cache[videoid] = {"timestamp": time.time(), "path": cache_path}
            
            # Clean cache if it's getting too large
            if len(processed_cache) > CACHE_SIZE:
                await cleanup_old_thumbnails()
            
            return cache_path
            
        results = VideosSearch(videoid, limit=1)
        async for result in results.next():
            try:
                title = result["title"][:50]
                title = re.sub(r"\W+", " ", title)
                title = title.title()
            except:
                title = "Unsupported Title"
            
            try:
                duration = result["duration"]
            except:
                duration = "Unknown Duration"
            
            try:
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            except:
                thumbnail = "https://te.legra.ph/file/d5b8b91d5d8093dd9bc64.jpg"
            
            try:
                result["viewCount"]["text"]
            except:
                pass
            
            try:
                result["channel"]["name"]
            except:
                pass
            
            thumbnail = await get_image(thumbnail)
            if not thumbnail:
                return "assets/Thumbnail.jpg"
            
            # Process image for better display
            image = Image.open(thumbnail)
            
            # Improved image processing for better quality
            
            # Resize and crop to 16:9 aspect ratio if needed
            width, height = image.size
            if width/height != 16/9:
                # Calculate target dimensions
                if width/height > 16/9:
                    # Image is wider than 16:9
                    new_width = int(height * 16/9)
                    left = (width - new_width) // 2
                    image = image.crop((left, 0, left + new_width, height))
                else:
                    # Image is taller than 16:9
                    new_height = int(width * 9/16)
                    top = (height - new_height) // 2
                    image = image.crop((0, top, width, top + new_height))
            
            # Resize to standard size for consistency
            image = image.resize((1280, 720), Image.Resampling.LANCZOS)
            
            # Enhanced image processing
            image = enhance_thumbnail(image)
            
            # Create a background with gradient
            background = Image.new("RGBA", (1280, 720), (0, 0, 0, 255))
            color = random_color()
            overlay = generate_gradient(1280, 720, (30, 30, 30, 220), (color[0], color[1], color[2], 80))
            
            # Blend the image with background
            background.paste(image, (0, 0))
            background = Image.alpha_composite(background.convert("RGBA"), overlay)
            
            # Add a green boundary
            background = add_green_boundary(background)
            
            # Use a larger portion of the screen for the image by reducing text area
            # Load logo for the profile pic - make it smaller and move it to top-left corner
            logo = "assets/logo.png"
            if os.path.exists(logo):
                circle_logo = crop_center_circle(Image.open(logo), 120)  # Smaller size
                # Position in the top-left corner with padding
                background.paste(circle_logo, (40, 40), circle_logo)
            
            # Load fonts
            try:
                font_file = "assets/font2.ttf"
                font_file_bold = "assets/font2.ttf"
                
                # Add title text with shadow - smaller and positioned better
                title_font = ImageFont.truetype(font_file_bold, 34)  # Reduced font size
                draw = ImageDraw.Draw(background)
                
                # Use a more compact layout for text to make image appear larger
                title_lines = truncate(title)
                
                # Position title at the top of the image for a more compact layout
                y_position = 45
                
                # Add a semi-transparent overlay just for the text area in top right
                text_overlay = Image.new("RGBA", (600, 130), (0, 0, 0, 180))
                background.paste(text_overlay, (640, 20), text_overlay)
                
                # Title alignment to the right side
                x_position = 680
                
                for line in title_lines:
                    if line:
                        # Add text shadow for readability
                        draw_text_with_shadow(
                            background, draw, 
                            (x_position, y_position),
                            line, title_font, "white"
                        )
                        y_position += 45
                
                # Add duration text
                duration_font = ImageFont.truetype(font_file, 26)  # Smaller font
                draw_text_with_shadow(
                    background, draw, 
                    (x_position, y_position + 5),
                    f"Duration: {duration}", duration_font, "white"
                )
                
                # Save optimized image
                if not os.path.exists("cache"):
                    os.makedirs("cache")
                
                background = background.convert("RGB")
                background.save(cache_path, format="PNG", optimize=True)
                
                # Add to cache dict for LRU tracking
                processed_cache[videoid] = {"timestamp": time.time(), "path": cache_path}
                
                # Clean cache if it's getting too large
                if len(processed_cache) > CACHE_SIZE:
                    await cleanup_old_thumbnails()
                
                return cache_path
            except Exception as e:
                print(f"Error in thumbnail text rendering: {e}")
                # If error in text, still try to save the image without text
                if not os.path.exists("cache"):
                    os.makedirs("cache")
                background = background.convert("RGB")
                background.save(cache_path, format="PNG", optimize=True)
                return cache_path
                
    except Exception as e:
        print(f"Error in thumbnail generation: {e}")
        return "assets/Thumbnail.jpg"

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
                        print(f"Removed old thumbnail: {file}")
                        
            # Also clean up the processed_cache to avoid memory leaks
            if len(processed_cache) > CACHE_SIZE:
                # Sort by last used timestamp and remove oldest entries
                items = list(processed_cache.items())
                items.sort(key=lambda x: x[1]["timestamp"])
                # Remove the oldest half
                for i in range(len(items) // 2):
                    processed_cache.pop(items[i][0], None)
                print(f"Cache optimized: removed {len(items) // 2} older thumbnail references")
                
        except Exception as e:
            logging.error(f"Error in cleanup: {e}")
        await asyncio.sleep(3600)  # Run every hour

# Memory management for thumbnail generation
async def optimize_memory_usage():
    """Periodically clear caches if memory usage is too high"""
    while True:
        try:
            # Get current memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # If memory usage is too high (>85%), clear caches
            if memory_percent > 85:
                # Clear LRU cache
                changeImageSize.cache_clear()
                get_text_dimensions.cache_clear()
                random_color.cache_clear()
                
                # Clear processed_cache
                processed_cache.clear()
                
                logging.info(f"Memory usage was high ({memory_percent}%). Cleared caches.")
                
                # Force garbage collection
                import gc
                gc.collect()
                
        except Exception as e:
            logging.error(f"Error in memory optimization: {e}")
        
        await asyncio.sleep(300)  # Check every 5 minutes
