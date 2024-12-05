import os
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from db import *

load_dotenv()

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Initialize the bot
bot = TelegramClient('TMP_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# make username global so that it is accessible under other events
global user_name
global user_id

@bot.on(events.NewMessage(pattern='/start'))
async def handle_start_command(event):
    sender = await event.get_sender()
    user_name = sender.username

    markup = event.client.build_reply_markup([
        [Button.text('Track a product')],
        [Button.text('See my tracklist')],
        [Button.text('Remove all products')],
        [Button.text('Remove a specific product')]
    ])
    await event.respond(
        f"Hello {user_name}, use the buttons below to interact with the bot.",
        buttons=markup
    )

@bot.on(events.NewMessage(pattern='Track a product'))
async def handle_track_button(event):
    set_status(event.sender_id, 'waiting_for_tag')
    await event.respond("Please enter the Product Tag to track:")

@bot.on(events.NewMessage)
async def handle_product_title(event):
    sender = await event.get_sender()
    
    user_data = get_user_data(event.sender_id)
    status = user_data.get("status")
    message = event.message.message.strip()
    
    # Make sure it's not one of the commands
    if message != 'Track a product' and message != 'See my tracklist' and message != 'Remove all products' and message != 'Remove a specific product':
        if status == 'waiting_for_tag':
            # Add the tag to the user's tracked tags
            add_tag(event.sender_id, message)

            await bot.send_message(sender, f"{message} has been added to your tracklist.")
            user_data = get_user_data(event.sender_id)
            tags = user_data.get("tags", [])
            tag_buttons = [[Button.inline(tag, data=tag)] for tag in tags]
            markup = event.client.build_reply_markup(tag_buttons)
            await bot.send_message(sender, "Your updated tracklist:", buttons=markup)

        elif status == 'removing_specific':
            remove_specific_tag(event.sender_id, message)
            await bot.send_message(sender, f"{message} has been removed from your tracklist.")
        

@bot.on(events.NewMessage(pattern='See my tracklist'))
async def handle_list_button(event):
    sender = await event.get_sender()
    user_data = get_user_data(event.sender_id)
    tags = user_data.get("tags", [])
    
    if tags:
        tag_buttons = [[Button.inline(tag, data=tag)] for tag in tags]
        markup = event.client.build_reply_markup(tag_buttons)
        await bot.send_message(sender, "Your updated tracklist:", buttons=markup)
    else:
        await event.respond("You are not tracking any product tags. Use 'Track a product' to start tracking.")

@bot.on(events.NewMessage(pattern='Remove all products'))
async def handle_remove_all_button(event):
    remove_all_tags(event.sender_id)
    await event.respond("All products have been removed from your tracklist.")

# Handle the command to remove a specific product
@bot.on(events.NewMessage(pattern='Remove a specific product'))
async def handle_remove_specific_button(event):
    # Set user status to indicate they are waiting for a specific tag
    set_status(event.sender_id, 'waiting_for_specific_tag')

    user_data = get_user_data(event.sender_id)
    tags = user_data.get("tags", [])
    
    if not tags:
        await event.respond("You are not tracking any product tags to remove.")
        return
    
    set_status(event.sender_id, 'removing_specific')
    tag_buttons = [[Button.inline(tag, data=tag)] for tag in tags]
    markup = event.client.build_reply_markup(tag_buttons)
    await event.respond("Select the product tag you want to remove:", buttons=markup)

# Handle the button clicks for tag selection
@bot.on(events.CallbackQuery)
async def handle_tag_selection(event):
    tag = event.data.decode("utf-8")  # Decode the button data
    user_data = get_user_data(event.sender_id)
    tags = user_data.get("tags", [])
    current_status = user_data.get("status")

    if current_status == 'removing_specific':
        if tag in user_data.get("tags", []):
            # Process the tag (e.g., remove it from user's tracked tags)
            remove_specific_tag(event.sender_id, tag)
            # save_user_data(event.sender_id, user_data)  # Save updated data
            user_data = get_user_data(event.sender_id)
            tags = user_data.get("tags", [])
            tag_buttons = [[Button.inline(tag, data=tag)] for tag in tags]
            markup = event.client.build_reply_markup(tag_buttons)
            # await event.respond("Select the product tag you want to remove:", buttons=markup)
            await event.edit(f"Removed the tag: {tag}\n\nYour updated tracklist is:", buttons=markup)
        else:
            await event.respond("Invalid tag or already removed.")

@bot.on(events.NewMessage(chats="@buy_smart_app"))
async def handle_product_update(event):
    # Fetch the channel message
    channel_message = event.message.message.strip()

    # Get all users and their tracked tags from the database
    all_users = get_all_users()  # You need to implement this function in `db.py`

    # Iterate through users and their tags
    for user_id, user_data in all_users.items():
        tags = user_data.get("tags", [])

        # Check if any tag matches the channel message
        for tag in tags:
            if tag in channel_message:
                try:
                    await bot.send_message(user_id, f"New update related to your tracked tag '{tag}':\n\n{channel_message}")
                except Exception as e:
                    print(f"Error sending message to {user_id}: {e}")


# Run the bot
print("Bot is running...")
bot.run_until_disconnected()
