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
    """Optimized thumbnail enhancement with increased brightness and contrast"""
    enhancers = [
        (ImageEnhance.Contrast, 1.5),    # Increased from 1.2
        (ImageEnhance.Sharpness, 1.3),   # Increased from 1.2
        (ImageEnhance.Brightness, 1.25), # Increased from 1.1
        (ImageEnhance.Color, 1.2)        # Added color enhancement
    ]
    
    for enhancer_class, factor in enhancers:
        image = enhancer_class(image).enhance(factor)
    return image

async def gen_thumb(videoid: str):
    try:
        # Check cache first to avoid reprocessing
        cache_path = f"cache/{videoid}_v7.png"
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
            image = Image.new("RGB", (1280, 720), (20, 20, 30))  # Darker blue-black background
            color = random_color()
            # Make a gradient background
            background = generate_gradient(1280, 720, (30, 30, 40), (color[0], color[1], color[2], 170))
            
            # Load a default icon
            icon_path = "assets/Telegram.png"
            if os.path.exists(icon_path):
                icon = Image.open(icon_path)
                # Make circular icon with enhanced border
                icon_size = 420  # Larger icon size for better visibility
                icon = crop_center_circle(icon, icon_size)
                # Center the icon (adjusted position to be higher up)
                background.paste(icon, (int((1280-icon_size)/2), int((720-icon_size)/2)-50), icon)
            
            # Add enhanced green boundary with increased visibility
            background = add_green_boundary(background, border_width=8)
            
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
            
        # Fix: Properly handle the VideosSearch coroutine with timeout
        try:
            vs = VideosSearch(videoid, limit=1)
            timeout_task = asyncio.create_task(asyncio.wait_for(vs.next(), 10.0))  # 10 second timeout
            result_data = await timeout_task
        except asyncio.TimeoutError:
            print(f"Timeout fetching video data for {videoid}")
            # Return default thumbnail on timeout
            default_thumb = "assets/Thumbnail.jpg"
            if not os.path.isfile(default_thumb):
                default_thumb = "AviaxMusic/assets/Thumbnail.jpg"
            return default_thumb
        except Exception as e:
            print(f"Error fetching video data: {e}")
            # Return default thumbnail on error
            default_thumb = "assets/Thumbnail.jpg"
            if not os.path.isfile(default_thumb):
                default_thumb = "AviaxMusic/assets/Thumbnail.jpg"
            return default_thumb
        
        if not result_data or not result_data.get("result"):
            # Return default thumbnail if no results
            default_thumb = "assets/Thumbnail.jpg"
            if not os.path.isfile(default_thumb):
                default_thumb = "AviaxMusic/assets/Thumbnail.jpg"
            return default_thumb
        
        # Get the first result
        result = result_data["result"][0]
        
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
            # Use a more reliable default thumbnail
            thumbnail = "https://te.legra.ph/file/d5b8b91d5d8093dd9bc64.jpg"
        
        # Get the image data
        thumbnail_data = await get_image(thumbnail)
        if not thumbnail_data:
            # Return default thumbnail if image fetch fails
            default_thumb = "assets/Thumbnail.jpg"
            if not os.path.isfile(default_thumb):
                default_thumb = "AviaxMusic/assets/Thumbnail.jpg"
            return default_thumb
        
        # Process image for better display
        try:
            image = Image.open(thumbnail_data)
        except Exception as e:
            print(f"Error opening thumbnail image: {e}")
            default_thumb = "assets/Thumbnail.jpg"
            if not os.path.isfile(default_thumb):
                default_thumb = "AviaxMusic/assets/Thumbnail.jpg"
            return default_thumb
        
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
        
        # Apply initial enhancement to the source image
        image = enhance_thumbnail(image)
        
        # Create a background with gradient - use darker base for better contrast
        background = Image.new("RGBA", (1280, 720), (0, 0, 0, 255))
        
        # Blend the image with background - use a larger portion of the screen
        background.paste(image, (0, 0))
        
        # Add a light overlay for better text readability
        color = random_color()
        overlay = generate_gradient(1280, 720, (10, 10, 20, 180), (color[0], color[1], color[2], 60))
        background = Image.alpha_composite(background.convert("RGBA"), overlay)
        
        # Add a green boundary with increased width for better visibility
        background = add_green_boundary(background, border_width=8)
        
        # Use a larger portion of the screen for the image by reducing text area
        # Load logo for the profile pic - make it smaller and move it to bottom-right corner
        logo = "assets/logo.png"
        if os.path.exists(logo):
            try:
                logo_img = Image.open(logo)
                circle_logo = crop_center_circle(logo_img, 110)  # Slightly larger for visibility
                # Position in the bottom-right corner with padding
                background.paste(circle_logo, (1140, 580), circle_logo)
            except Exception as e:
                print(f"Error processing logo: {e}")
        
        # Load fonts
        try:
            font_file = "assets/font2.ttf"
            font_file_bold = "assets/font2.ttf"
            
            # Add title text with shadow - better positioned and more visible
            title_font = ImageFont.truetype(font_file_bold, 38)  # Larger font size for better visibility
            draw = ImageDraw.Draw(background)
            
            # Use a more compact layout for text to make image appear larger
            title_lines = truncate(title)
            
            # Position title at the top of the image for a more compact layout
            y_position = 25
            
            # Add a semi-transparent overlay just for the text area in top - darker for better contrast
            text_overlay = Image.new("RGBA", (1280, 120), (0, 0, 0, 210))
            background.paste(text_overlay, (0, 0), text_overlay)
            
            # Title alignment to the center with enhanced shadow
            for line in title_lines:
                if line:
                    # Get width for center alignment
                    text_width, _ = get_text_dimensions(line, title_font)
                    x_position = (1280 - text_width) // 2
                    
                    # Add text shadow for readability - larger offset and more blur
                    draw_text_with_shadow(
                        background, draw, 
                        (x_position, y_position),
                        line, title_font, "white",
                        shadow_offset=(4, 4),
                        shadow_blur=7
                    )
                    y_position += 48  # Increased spacing
            
            # Add duration text with enhanced visibility
            duration_font = ImageFont.truetype(font_file, 30)  # Larger for better visibility
            duration_text = f"Duration: {duration}"
            dur_width, _ = get_text_dimensions(duration_text, duration_font)
            x_position = (1280 - dur_width) // 2
            
            draw_text_with_shadow(
                background, draw, 
                (x_position, y_position + 5),
                duration_text, duration_font, "white",
                shadow_offset=(4, 4),
                shadow_blur=7
            )
            
            # Save optimized image
            if not os.path.exists("cache"):
                os.makedirs("cache")
            
            background = background.convert("RGB")
            background.save(cache_path, format="PNG", optimize=True, quality=95)  # Higher quality
            
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
        # Return a default thumbnail that definitely exists
        default_thumb = "assets/Thumbnail.jpg"
        if not os.path.isfile(default_thumb):
            default_thumb = "AviaxMusic/assets/Thumbnail.jpg"
        return default_thumb

# Fix: Update the get_image function to handle errors better and retry on failure
async def get_image(url):
    attempts = 3  # Try up to 3 times
    
    for attempt in range(attempts):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        # Save to a temporary file
                        temp_file = f"cache/temp_{int(time.time())}.jpg"
                        if not os.path.exists("cache"):
                            os.makedirs("cache")
                        async with aiofiles.open(temp_file, "wb") as f:
                            await f.write(data)
                        return temp_file
                    else:
                        print(f"Error fetching image (attempt {attempt+1}/{attempts}): HTTP {resp.status}")
                        if attempt == attempts - 1:  # Last attempt
                            return None
                        await asyncio.sleep(1)  # Wait before retrying
        except Exception as e:
            print(f"Error downloading image (attempt {attempt+1}/{attempts}): {e}")
            if attempt == attempts - 1:  # Last attempt
                return None
            await asyncio.sleep(1)  # Wait before retrying
    
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
