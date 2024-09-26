import asyncio
from io import BytesIO
from os import remove

from skimage import io as sk_io
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = ''

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'ppm']
file_storage = {}


@dp.message(CommandStart())
async def send_welcome(message: Message):
    await message.answer("Привет! Пришлите мне изображение, и я конвертирую его в другой формат.")


@dp.message(F.photo)
async def handle_image(message: Message):
    file_id = message.photo[-1].file_id
    message_id = message.message_id
    file_storage[message_id] = file_id

    keyboard = InlineKeyboardBuilder()
    for fmt in SUPPORTED_FORMATS:
        keyboard.add(InlineKeyboardButton(text=fmt, callback_data=f"{fmt}:{message_id}"))
    keyboard.adjust(2)

    await message.answer("Выберите формат для конвертации изображения:", reply_markup=keyboard.as_markup())


@dp.callback_query(F.data)
async def process_callback(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    format_to_convert, message_id_str = callback_query.data.split(':')
    message_id = int(message_id_str)
    file_id = file_storage.get(message_id)

    if file_id:
        file_info = await bot.get_file(file_id)
        file = await bot.download_file(file_info.file_path)
        img = sk_io.imread(BytesIO(file.read()))
        output_path = f'{message_id}.{format_to_convert}'
        sk_io.imsave(output_path, img)

        input_file = FSInputFile(output_path)
        await bot.send_document(callback_query.from_user.id, input_file)

        del file_storage[message_id]
        remove(output_path)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())