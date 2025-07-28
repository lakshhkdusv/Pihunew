from SHUKLAMUSIC import app
from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from os import environ, remove, path
from typing import Union, Optional
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from SHUKLAMUSIC.utils.image_validation import safe_download_media, safe_remove_file
import asyncio

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
            if not path.exists(profile_path):
                print(f"Profile image file does not exist: {profile_path}")
            else:
                # Check if file is empty or too small (corrupted)
                file_size = path.getsize(profile_path)
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
            # Clean up the downloaded profile image file
            safe_remove_file(profile_path)

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

# --------------------------------------------------------------------------------- #

bg_path = "SHUKLAMUSIC/assets/userinfo.png"
font_path = "SHUKLAMUSIC/assets/hiroko.ttf"

# --------------------------------------------------------------------------------- #

# -------------

@app.on_chat_member_updated(filters.group, group=20)
async def member_has_left(client, member: ChatMemberUpdated):

    if (
        not member.new_chat_member
        and member.old_chat_member.status not in {
            "banned", "left", "restricted"
        }
        and member.old_chat_member
    ):
        pass
    else:
        return

    user = (
        member.old_chat_member.user
        if member.old_chat_member
        else member.from_user
    )

    # Check if the user has a profile photo
    if user.photo and user.photo.big_file_id:
        try:
            # Download the profile photo with error handling and validation
            photo = await safe_download_media(user.photo.big_file_id)
            
            welcome_photo = await get_userinfo_img(
                bg_path=bg_path,
                font_path=font_path,
                user_id=user.id,
                profile_path=photo,
            )
            
            # Check if image generation was successful
            if not welcome_photo:
                print(f"Failed to generate user info image for user {user.id}")
                # Fallback: send a simple text message instead
                caption = f"**❅─────✧❅✦❅✧─────❅**\n\n**๏ ᴀ ᴍᴇᴍʙᴇʀ ʟᴇғᴛ ᴛʜᴇ ɢʀᴏᴜᴘ🥀**\n\n**➻** {member.old_chat_member.user.mention}\n\n**๏ ᴏᴋ ʙʏᴇ ᴅᴇᴀʀ ᴀɴᴅ ʜᴏᴘᴇ ᴛᴏ sᴇᴇ ʏᴏᴜ ᴀɢᴀɪɴ ɪɴ ᴛʜɪs ᴄᴜᴛᴇ ɢʀᴏᴜᴘ ᴡɪᴛʜ ʏᴏᴜʀ ғʀɪᴇɴᴅs✨**\n\n**ㅤ•─╼⃝𖠁 ʙʏᴇ ♡︎ ʙᴀʙʏ 𖠁⃝╾─•**"
                button_text = "๏ ᴠɪᴇᴡ ᴜsᴇʀ ๏"
                deep_link = f"tg://openmessage?user_id={user.id}"
                
                message = await client.send_message(
                    chat_id=member.chat.id,
                    text=caption,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(button_text, url=deep_link)]
                    ])
                )
                
                # Schedule a task to delete the message after 30 seconds
                async def delete_message():
                    await asyncio.sleep(30)
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Error deleting message: {e}")
                asyncio.create_task(delete_message())
                return
        
            caption = f"**❅─────✧❅✦❅✧─────❅**\n\n**๏ ᴀ ᴍᴇᴍʙᴇʀ ʟᴇғᴛ ᴛʜᴇ ɢʀᴏᴜᴘ🥀**\n\n**➻** {member.old_chat_member.user.mention}\n\n**๏ ᴏᴋ ʙʏᴇ ᴅᴇᴀʀ ᴀɴᴅ ʜᴏᴘᴇ ᴛᴏ sᴇᴇ ʏᴏᴜ ᴀɢᴀɪɴ ɪɴ ᴛʜɪs ᴄᴜᴛᴇ ɢʀᴏᴜᴘ ᴡɪᴛʜ ʏᴏᴜʀ ғʀɪᴇɴᴅs✨**\n\n**ㅤ•─╼⃝𖠁 ʙʏᴇ ♡︎ ʙᴀʙʏ 𖠁⃝╾─•**"
            button_text = "๏ ᴠɪᴇᴡ ᴜsᴇʀ ๏"

            # Generate a deep link to open the user's profile
            deep_link = f"tg://openmessage?user_id={user.id}"

            # Send the message with the photo, caption, and button
            message = await client.send_photo(
                chat_id=member.chat.id,
                photo=welcome_photo,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(button_text, url=deep_link)]
                ])
            )

            # Clean up the generated image file
            safe_remove_file(welcome_photo)

            # Schedule a task to delete the message after 30 seconds
            async def delete_message():
                await asyncio.sleep(30)
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")

            # Run the task
            asyncio.create_task(delete_message())
            
        except RPCError as e:
            print(f"RPCError in member_has_left: {e}")
            return
        except Exception as e:
            print(f"Unexpected error in member_has_left: {e}")
            return
    else:
        # Handle the case where the user has no profile photo
        print(f"User {user.id} has no profile photo. Sending text message.")
        try:
            # Create image without profile photo
            welcome_photo = await get_userinfo_img(
                bg_path=bg_path,
                font_path=font_path,
                user_id=user.id,
                profile_path=None,
            )
            
            if welcome_photo:
                caption = f"**❅─────✧❅✦❅✧─────❅**\n\n**๏ ᴀ ᴍᴇᴍʙᴇʀ ʟᴇғᴛ ᴛʜᴇ ɢʀᴏᴜᴘ🥀**\n\n**➻** {member.old_chat_member.user.mention}\n\n**๏ ᴏᴋ ʙʏᴇ ᴅᴇᴀʀ ᴀɴᴅ ʜᴏᴘᴇ ᴛᴏ sᴇᴇ ʏᴏᴜ ᴀɢᴀɪɴ ɪɴ ᴛʜɪs ᴄᴜᴛᴇ ɢʀᴏᴜᴘ ᴡɪᴛʜ ʏᴏᴜʀ ғʀɪᴇɴᴅs✨**\n\n**ㅤ•─╼⃝𖠁 ʙʏᴇ ♡︎ ʙᴀʙʏ 𖠁⃝╾─•**"
                button_text = "๏ ᴠɪᴇᴡ ᴜsᴇʀ ๏"
                deep_link = f"tg://openmessage?user_id={user.id}"

                # Send the message with the photo, caption, and button
                message = await client.send_photo(
                    chat_id=member.chat.id,
                    photo=welcome_photo,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(button_text, url=deep_link)]
                    ])
                )

                # Clean up the generated image file
                safe_remove_file(welcome_photo)

                # Schedule a task to delete the message after 30 seconds
                async def delete_message():
                    await asyncio.sleep(30)
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Error deleting message: {e}")
                asyncio.create_task(delete_message())
            else:
                # Fallback to text message if image generation fails
                caption = f"**❅─────✧❅✦❅✧─────❅**\n\n**๏ ᴀ ᴍᴇᴍʙᴇʀ ʟᴇғᴛ ᴛʜᴇ ɢʀᴏᴜᴘ🥀**\n\n**➻** {member.old_chat_member.user.mention}\n\n**๏ ᴏᴋ ʙʏᴇ ᴅᴇᴀʀ ᴀɴᴅ ʜᴏᴘᴇ ᴛᴏ sᴇᴇ ʏᴏᴜ ᴀɢᴀɪɴ ɪɴ ᴛʜɪs ᴄᴜᴛᴇ ɢʀᴏᴜᴘ ᴡɪᴛʜ ʏᴏᴜʀ ғʀɪᴇɴᴅs✨**\n\n**ㅤ•─╼⃝𖠁 ʙʏᴇ ♡︎ ʙᴀʙʏ 𖠁⃝╾─•**"
                button_text = "๏ ᴠɪᴇᴡ ᴜsᴇʀ ๏"
                deep_link = f"tg://openmessage?user_id={user.id}"
                
                message = await client.send_message(
                    chat_id=member.chat.id,
                    text=caption,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(button_text, url=deep_link)]
                    ])
                )
                
                # Schedule a task to delete the message after 30 seconds
                async def delete_message():
                    await asyncio.sleep(30)
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Error deleting message: {e}")
                asyncio.create_task(delete_message())
                
        except Exception as e:
            print(f"Error handling user without profile photo: {e}")
            return
        
