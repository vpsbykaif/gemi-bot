from typing import Any, Dict
from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold
from asyncio.futures import Future

from bot.middlewares import PhotoDownloadMiddleware
from chat.service import ChatService

# All handlers should be attached to the Router (or Dispatcher)
router = Router(name='/')
# router.message.middleware(PhotoDownloadMiddleware())

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!", parse_mode=ParseMode.HTML)


@router.message()
async def echo_handler(message: Message, state: FSMContext, chat: ChatService) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    sent: Message | None = None
    try:
        # Send a reply to the received message
        sent = await message.reply('Thinking...')
        response = ''
        async for reply in chat.gen_response_stream(message.text):
            response = response + reply
            sent = await sent.edit_text(text=response)
    except Exception as e:
        # But not all the types is supported to be copied so need to handle it
        if sent != None:
            await sent.edit_text(text=f'Oops! Failed...\n\n{type(e).__name__}: {e}', parse_mode=ParseMode.HTML)
        else:
            await message.reply(f'Oops! Failed...\n\n{type(e).__name__}: {e}', parse_mode=ParseMode.HTML)
