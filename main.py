import os
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from db import *

# Load environment variables
load_dotenv()

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Initialize the bot
bot = TelegramClient('TMP_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Event Handlers

@bot.on(events.NewMessage(pattern='/start'))
async def handle_start_command(event):
    """
    Handle the /start command to greet the user and display options.
    """
    sender = await event.get_sender()
    user_name = sender.username or "User"  # Handle case where username might not be set

    # Create interactive buttons
    buttons = [
        [Button.text('Track a product')],
        [Button.text('See my tracklist')],
        [Button.text('Remove all products')],
        [Button.text('Remove a specific product')],
    ]
    markup = event.client.build_reply_markup(buttons)
    
    await event.respond(
        f"Hello {user_name}, use the buttons below to interact with the bot.",
        buttons=markup
    )


@bot.on(events.NewMessage(pattern='Track a product'))
async def handle_track_button(event):
    """
    Initiates tracking by prompting the user for a product tag.
    """
    set_status(event.sender_id, 'waiting_for_tag')
    await event.respond("Please enter the product tag you want to track:")


@bot.on(events.NewMessage)
async def handle_user_messages(event):
    """
    Handles generic user messages based on the user's status in the database.
    """
    sender = await event.get_sender()
    user_data = get_user_data(event.sender_id)  # Fetch user data from database
    status = user_data.get("status")
    message = event.message.message.strip()

    if message not in {'Track a product', 'See my tracklist', 'Remove all products', 'Remove a specific product'}:
        if status == 'waiting_for_tag':
            add_tag(event.sender_id, message)
            await event.respond(f"'{message}' has been added to your tracklist.")
            
            # Display updated tracklist
            tags = get_user_data(event.sender_id).get("tags", [])
            if tags:
                buttons = [[Button.inline(tag, data=tag)] for tag in tags]
                markup = event.client.build_reply_markup(buttons)
                await event.respond("Your updated tracklist:", buttons=markup)
        elif status == 'removing_specific':
            remove_specific_tag(event.sender_id, message)
            await event.respond(f"'{message}' has been removed from your tracklist.")


@bot.on(events.NewMessage(pattern='See my tracklist'))
async def handle_list_button(event):
    """
    Displays the user's current tracklist.
    """
    user_data = get_user_data(event.sender_id)
    tags = user_data.get("tags", [])

    if tags:
        buttons = [[Button.inline(tag, data=tag)] for tag in tags]
        markup = event.client.build_reply_markup(buttons)
        await event.respond("Your tracked products:", buttons=markup)
    else:
        await event.respond("You are not tracking any products. Use 'Track a product' to start.")


@bot.on(events.NewMessage(pattern='Remove all products'))
async def handle_remove_all_button(event):
    """
    Removes all tracked products for the user.
    """
    remove_all_tags(event.sender_id)
    await event.respond("All products have been removed from your tracklist.")


@bot.on(events.NewMessage(pattern='Remove a specific product'))
async def handle_remove_specific_button(event):
    """
    Prompts the user to select a product tag to remove.
    """
    user_data = get_user_data(event.sender_id)
    tags = user_data.get("tags", [])

    if tags:
        set_status(event.sender_id, 'removing_specific')
        buttons = [[Button.inline(tag, data=tag)] for tag in tags]
        markup = event.client.build_reply_markup(buttons)
        await event.respond("Select the product tag you want to remove:", buttons=markup)
    else:
        await event.respond("You are not tracking any products.")


@bot.on(events.CallbackQuery)
async def handle_tag_selection(event):
    """
    Handles button clicks for selecting a specific tag.
    """
    tag = event.data.decode("utf-8")
    user_data = get_user_data(event.sender_id)

    if tag in user_data.get("tags", []):
        remove_specific_tag(event.sender_id, tag)
        updated_tags = get_user_data(event.sender_id).get("tags", [])
        
        if updated_tags:
            buttons = [[Button.inline(tag, data=tag)] for tag in updated_tags]
            markup = event.client.build_reply_markup(buttons)
            await event.edit(f"Removed '{tag}'. Your updated tracklist:", buttons=markup)
        else:
            await event.edit(f"Removed '{tag}'. You have no products left in your tracklist.")
    else:
        await event.respond("Invalid tag or already removed.")


@bot.on(events.NewMessage(chats="@buy_smart_app"))
async def handle_product_update(event):
    """
    Monitors the specified channel for product updates and notifies users.
    """
    channel_message = event.message.message.strip()
    all_users = get_all_users()  # Retrieve all users from the database

    for user_id, user_data in all_users.items():
        tags = user_data.get("tags", [])
        for tag in tags:
            if tag in channel_message:
                try:
                    await bot.send_message(user_id, f"New update related to your tracked tag '{tag}':\n\n{channel_message}")
                except Exception as e:
                    print(f"Error sending message to {user_id}: {e}")


# Run the bot
print("Bot is running...")
bot.run_until_disconnected()
