import asyncio, os, time, aiohttp
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from asyncio import sleep
from SHUKLAMUSIC import app
from pyrogram import filters, Client, enums
from pyrogram.enums import ParseMode
from pyrogram.types import *
from typing import Union, Optional
import os
import random

random_photo = [
    "https://telegra.ph/file/1949480f01355b4e87d26.jpg",
    "https://telegra.ph/file/3ef2cc0ad2bc548bafb30.jpg",
    "https://telegra.ph/file/a7d663cd2de689b811729.jpg",
    "https://telegra.ph/file/6f19dc23847f5b005e922.jpg",
    "https://telegra.ph/file/2973150dd62fd27a3a6ba.jpg",
]

# --------------------------------------------------------------------------------- #


get_font = lambda font_size, font_path: ImageFont.truetype(font_path, font_size)
resize_text = (
    lambda text_size, text: (text[:text_size] + "...").upper()
    if len(text) > text_size
    else text.upper()
)

# --------------------------------------------------------------------------------- #


async def get_userinfo_img(
    bg_path: str,
    font_path: str,
    user_id: Union[int, str],    
    profile_path: Optional[str] = None
):
    try:
        bg = Image.open(bg_path)
    except (UnidentifiedImageError, FileNotFoundError) as e:
        print(f"Error opening background image {bg_path}: {e}")
        return None

    if profile_path:
        try:
            # Validate that the profile image file exists and is readable
            if not os.path.exists(profile_path):
                print(f"Profile image file does not exist: {profile_path}")
            else:
                # Check if file is empty or too small (corrupted)
                file_size = os.path.getsize(profile_path)
                if file_size < 100:  # Less than 100 bytes is likely corrupted
                    print(f"Profile image file is too small (corrupted): {profile_path} - {file_size} bytes")
                    return None
                
                # Try to verify it's a valid image before opening
                try:
                    # First, try to open and verify the image
                    with Image.open(profile_path) as test_img:
                        test_img.verify()  # This will raise an exception if the image is corrupted
                    
                    # If verification passes, open the image for processing
                    img = Image.open(profile_path)
                    
                    # Check if image has valid dimensions
                    if img.size[0] <= 0 or img.size[1] <= 0:
                        print(f"Profile image has invalid dimensions: {img.size}")
                        img.close()
                        return None
                    
                    mask = Image.new("L", img.size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.pieslice([(0, 0), img.size], 0, 360, fill=255)

                    circular_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    circular_img.paste(img, (0, 0), mask)
                    resized = circular_img.resize((400, 400))
                    bg.paste(resized, (440, 160), resized)
                    img.close()  # Close the image to free memory
                    
                except (UnidentifiedImageError, OSError, ValueError) as e:
                    print(f"Invalid or corrupted profile image {profile_path}: {e}")
                    # Continue without profile image if there's an error
                    
        except Exception as e:
            print(f"Unexpected error processing profile image {profile_path}: {e}")
            # Continue without profile image if there's an error
        finally:
            # Clean up the downloaded profile image file if it exists
            try:
                if profile_path and os.path.exists(profile_path):
                    os.remove(profile_path)
            except OSError as e:
                print(f"Error removing temporary file {profile_path}: {e}")

    try:
        img_draw = ImageDraw.Draw(bg)
        font = get_font(46, font_path)
        img_draw.text(
            (529, 627),
            text=str(user_id).upper(),
            font=font,
            fill=(255, 255, 255),
        )

        path_out = f"./userinfo_img_{user_id}.png"
        bg.save(path_out)
        bg.close()  # Close the image to free memory
        return path_out
    except Exception as e:
        print(f"Error creating user info image: {e}")
        return None

    img_draw = ImageDraw.Draw(bg)

    img_draw.text(
        (529, 627),
        text=str(user_id).upper(),
        font=get_font(46, font_path),
        fill=(255, 255, 255),
    )


    path = f"./userinfo_img_{user_id}.png"
    bg.save(path)
    return path
   

# --------------------------------------------------------------------------------- #

bg_path = "SHUKLAMUSIC/assets/userinfo.png"
font_path = "SHUKLAMUSIC/assets/hiroko.ttf"

# --------------------------------------------------------------------------------- #


INFO_TEXT = """**
[ᯤ] 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗡𝗧𝗢𝗡 [ᯤ]

[🍹] ᴜsᴇʀ ɪᴅ ‣ **`{}`
**[💓] ғɪʀsᴛ ɴᴀᴍᴇ ‣ **{}
**[💗] ʟᴀsᴛ ɴᴀᴍᴇ ‣ **{}
**[🍷] ᴜsᴇʀɴᴀᴍᴇ ‣ **`{}`
**[🍬] ᴍᴇɴᴛɪᴏɴ ‣ **{}
**[🍁] ʟᴀsᴛ sᴇᴇɴ ‣ **{}
**[🎫] ᴅᴄ ɪᴅ ‣ **{}
**[🗨️] ʙɪᴏ ‣ **`{}`

**☉━━☉━━☉━侖━☉━━☉━━☉**
"""

# --------------------------------------------------------------------------------- #

async def userstatus(user_id):
   try:
      user = await app.get_users(user_id)
      x = user.status
      if x == enums.UserStatus.RECENTLY:
         return "Recently."
      elif x == enums.UserStatus.LAST_WEEK:
          return "Last week."
      elif x == enums.UserStatus.LONG_AGO:
          return "Long time ago."
      elif x == enums.UserStatus.OFFLINE:
          return "Offline."
      elif x == enums.UserStatus.ONLINE:
         return "Online."
   except:
        return "**sᴏᴍᴇᴛʜɪɴɢ ᴡʀᴏɴɢ ʜᴀᴘᴘᴇɴᴇᴅ !**"
    

# --------------------------------------------------------------------------------- #



@app.on_message(filters.command(["info", "userinfo"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]))
async def userinfo(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not message.reply_to_message and len(message.command) == 2:
        try:
            user_id = message.text.split(None, 1)[1]
            user_info = await app.get_chat(user_id)
            user = await app.get_users(user_id)
            status = await userstatus(user.id)
            id = user_info.id
            dc_id = user.dc_id
            first_name = user_info.first_name 
            last_name = user_info.last_name if user_info.last_name else "No last name"
            username = user_info.username if user_info.username else "No Username"
            mention = user.mention
            bio = user_info.bio if user_info.bio else "No bio set"
            
            if user.photo:
                # User has a profile photo
                photo = await app.download_media(user.photo.big_file_id)
                welcome_photo = await get_userinfo_img(
                    bg_path=bg_path,
                    font_path=font_path,
                    user_id=user.id,
                    profile_path=photo,
                )
            else:
                # User doesn't have a profile photo, use random_photo directly
                welcome_photo = random.choice(random_photo)
                
            await app.send_photo(chat_id, photo=welcome_photo, caption=INFO_TEXT.format(
                id, first_name, last_name, username, mention, status, dc_id, bio), reply_to_message_id=message.id)
        except Exception as e:
            await message.reply_text(str(e))        
      
    elif not message.reply_to_message:
        try:
            user_info = await app.get_chat(user_id)
            user = await app.get_users(user_id)
            status = await userstatus(user.id)
            id = user_info.id
            dc_id = user.dc_id
            first_name = user_info.first_name 
            last_name = user_info.last_name if user_info.last_name else "No last name"
            username = user_info.username if user_info.username else "No Username"
            mention = user.mention
            bio = user_info.bio if user_info.bio else "No bio set"
            
            if user.photo:
                # User has a profile photo
                photo = await app.download_media(user.photo.big_file_id)
                welcome_photo = await get_userinfo_img(
                    bg_path=bg_path,
                    font_path=font_path,
                    user_id=user.id,
                    profile_path=photo,
                )
            else:
                # User doesn't have a profile photo, use random_photo directly
                welcome_photo = random.choice(random_photo)
                
            await app.send_photo(chat_id, photo=welcome_photo, caption=INFO_TEXT.format(
                id, first_name, last_name, username, mention, status, dc_id, bio), reply_to_message_id=message.id)
        except Exception as e:
            await message.reply_text(str(e))

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        try:
            user_info = await app.get_chat(user_id)
            user = await app.get_users(user_id)
            status = await userstatus(user.id)
            id = user_info.id
            dc_id = user.dc_id
            first_name = user_info.first_name 
            last_name = user_info.last_name if user_info.last_name else "No last name"
            username = user_info.username if user_info.username else "No Username"
            mention = user.mention
            bio = user_info.bio if user_info.bio else "No bio set"
            
            if user.photo:
                # User has a profile photo
                photo = await app.download_media(user.photo.big_file_id)
                welcome_photo = await get_userinfo_img(
                    bg_path=bg_path,
                    font_path=font_path,
                    user_id=user.id,
                    profile_path=photo,
                )
            else:
                # User doesn't have a profile photo, use random_photo directly
                welcome_photo = random.choice(random_photo)
                
            await app.send_photo(chat_id, photo=welcome_photo, caption=INFO_TEXT.format(
                id, first_name, last_name, username, mention, status, dc_id, bio), reply_to_message_id=message.id)
        except Exception as e:
            await message.reply_text(str(e))
                
