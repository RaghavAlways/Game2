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

logging.basicConfig(level=logging.INFO)

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage

def truncate(text):
    list = text.split(" ")
    text1 = ""
    text2 = ""    
    for i in list:
        if len(text1) + len(i) < 30:        
            text1 += " " + i
        elif len(text2) + len(i) < 30:       
            text2 += " " + i

    text1 = text1.strip()
    text2 = text2.strip()     
    return [text1,text2]

def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def generate_gradient(width, height, start_color, end_color):
    base = Image.new('RGBA', (width, height), start_color)
    top = Image.new('RGBA', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(60 * (y / height))] * width)
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
    
    img = img.resize((output_size - 2*border, output_size - 2*border))
    
    
    final_img = Image.new("RGBA", (output_size, output_size), border_color)
    
    
    mask_main = Image.new("L", (output_size - 2*border, output_size - 2*border), 0)
    draw_main = ImageDraw.Draw(mask_main)
    draw_main.ellipse((0, 0, output_size - 2*border, output_size - 2*border), fill=255)
    
    final_img.paste(img, (border, border), mask_main)
    
    
    mask_border = Image.new("L", (output_size, output_size), 0)
    draw_border = ImageDraw.Draw(mask_border)
    draw_border.ellipse((0, 0, output_size, output_size), fill=255)
    
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
    """Enhance thumbnail with cool effects"""
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.2)
    
    # Slightly increase brightness
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.1)
    
    return image

async def gen_thumb(videoid: str):
    try:
        if os.path.isfile(f"cache/{videoid}_v4.png"):
            return f"cache/{videoid}_v4.png"

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            title = result.get("title")
            if title:
                title = re.sub("\W+", " ", title).title()
            else:
                title = "Unsupported Title"
            duration = result.get("duration")
            if not duration:
                duration = "Live"
            thumbnail_data = result.get("thumbnails")
            if thumbnail_data:
                thumbnail = thumbnail_data[0]["url"].split("?")[0]
            else:
                thumbnail = None
            views_data = result.get("viewCount")
            if views_data:
                views = views_data.get("short")
                if not views:
                    views = "Unknown Views"
            else:
                views = "Unknown Views"
            channel_data = result.get("channel")
            if channel_data:
                channel = channel_data.get("name")
                if not channel:
                    channel = "Unknown Channel"
            else:
                channel = "Unknown Channel"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                    await f.write(await resp.read())
                    await f.close()

        youtube = Image.open(f"cache/thumb{videoid}.png")
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")
        
        # Apply enhanced effects
        background = enhance_thumbnail(image2)
        
        # Add blur effect
        background = background.filter(filter=ImageFilter.BoxBlur(20))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        
        # Add gradient with random colors
        start_gradient_color = random_color()
        end_gradient_color = random_color()
        gradient_image = generate_gradient(1280, 720, start_gradient_color, end_gradient_color)
        background = Image.blend(background, gradient_image, alpha=0.2)
        
        # Add green boundary with glow
        background = add_green_boundary(background, border_width=5, border_color=(0, 255, 0, 180))
        
        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype("AviaxMusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("AviaxMusic/assets/font.ttf", 30)
        title_font = ImageFont.truetype("AviaxMusic/assets/font3.ttf", 45)

        # Create enhanced circular thumbnail
        circle_thumbnail = crop_center_circle(youtube, 400, 20, start_gradient_color)
        circle_thumbnail = circle_thumbnail.resize((400, 400))
        circle_position = (120, 160)
        background.paste(circle_thumbnail, circle_position, circle_thumbnail)

        # Add text with shadow effects
        text_x_position = 565
        title1 = truncate(title)
        draw_text_with_shadow(background, draw, (text_x_position, 180), title1[0], title_font, (255, 255, 255))
        draw_text_with_shadow(background, draw, (text_x_position, 230), title1[1], title_font, (255, 255, 255))
        draw_text_with_shadow(background, draw, (text_x_position, 320), f"{channel}  |  {views[:23]}", arial, (255, 255, 255))

        # Add enhanced progress line
        line_length = 580
        line_color = (0, 255, 0, 180)  # Green color matching boundary

        if duration != "Live":
            color_line_percentage = random.uniform(0.15, 0.85)
            color_line_length = int(line_length * color_line_percentage)
            white_line_length = line_length - color_line_length

            # Draw progress line with glow effect
            glow = Image.new('RGBA', background.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            
            # Draw colored part
            glow_draw.line(
                [(text_x_position, 380), (text_x_position + color_line_length, 380)],
                fill=line_color,
                width=4
            )
            
            # Draw white part
            glow_draw.line(
                [(text_x_position + color_line_length, 380), (text_x_position + line_length, 380)],
                fill=(200, 200, 200, 180),
                width=4
            )
            
            # Apply glow
            glow = glow.filter(ImageFilter.GaussianBlur(radius=2))
            background = Image.alpha_composite(background, glow)

            # Add duration text with shadow
            draw_text_with_shadow(background, draw, (text_x_position, 400), duration, arial, (255, 255, 255))

        background = background.convert("RGB")
        background.save(f"cache/{videoid}_v4.png")
        return f"cache/{videoid}_v4.png"

    except Exception as e:
        logging.error(f"Error generating thumbnail: {e}")
        return None
