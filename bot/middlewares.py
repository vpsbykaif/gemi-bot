import asyncio
from typing import Any, Awaitable, Callable, Dict, Union
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.utils.markdown import italic
from io import BytesIO
from PIL.Image import Image, open

class PromptGenMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __msg_to_prompt__(self, msg: Message):
        prompts: list[Union[str, Image]] = []
        
        if (msg.photo and len(msg.photo) > 0):
            msg.photo.sort(key=lambda ps: ps.file_size)
            limit_size = [p for p in msg.photo if p.file_size <= 100000] # limit to 200kb
            photo_id = limit_size[-1].file_id
            photo_bytes = BytesIO()
            photo_bytes = await msg.bot.download(photo_id, photo_bytes)
            prompts.append(open(photo_bytes))
        
        if (msg.text and len(msg.text) > 0):
            prompts.append(msg.text)

        return prompts

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        sent = await event.reply(italic('Downloading message...'))
        prompts: list[Union[str, Image]] = []
        tasks: list[asyncio.Task] = []

        reply_of = event.reply_to_message
        if (reply_of):
            tasks.append(asyncio.create_task(self.__msg_to_prompt__(reply_of)))
            tasks[-1].add_done_callback(lambda p: prompts.extend(p.result()))

        tasks.append(asyncio.create_task(self.__msg_to_prompt__(event)))
        tasks[-1].add_done_callback(lambda p: prompts.extend(p.result()))

        await asyncio.gather(*tasks)
        data['sent'] = sent
        data['prompts'] = prompts

        return await handler(event, data)