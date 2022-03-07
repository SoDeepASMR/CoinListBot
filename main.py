import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import config

bot = Bot(config.token)
dp = Dispatcher(bot, storage=MemoryStorage())

test_data = None


class RegStates(StatesGroup):
    wait_nationality = State()
    wait_fullname = State()
    wait_number = State()
    wait_address = State()
    wait_index = State()


async def deleter(start_id: int, chat_id: int) -> None:
    for _ in range(start_id, start_id - 20, -1):
        try:
            await bot.delete_message(chat_id, _)
        except Exception:
            pass


async def reg_start(message: types.message):
    global test_data
    try:
        file = open('users.txt', 'r', encoding='utf-8')
        test_data = [_.strip() for _ in file.readlines()]
        file.close()
    except FileNotFoundError:
        pass

    if message.chat.username:
        if '@' + message.chat.username in test_data:
            await message.answer(f'Извините, но вы уже давали свои данные {random.choice(config.lying_reaction)}', reply_markup=main_buttons(2))
            await deleter(message.message_id, message.chat.id)
            return

    await message.answer('Введите, пожалуйста, свою национальность (страну)')
    await RegStates.wait_nationality.set()
    await deleter(message.message_id, message.chat.id)


@dp.message_handler(state=RegStates.wait_nationality)
async def nationality(message: types.message, state: FSMContext):
    if message.text.lower() in 'россиярашкарусскийрашароссийская федерация':
        await message.answer(f'Извините, но регистрация недоступна для граждан РФ {random.choice(config.bad_reaction)}', reply_markup=main_buttons(2))
        await state.finish()
        return

    elif message.text.lower() in config.countries:
        await state.update_data(profile=None)

        if message.chat.username:
            profile = '@' + message.chat.username
            await state.update_data(profile=profile)

        await state.update_data(nationality=message.text.lower())
        await RegStates.next()
        await message.answer('Введите полное ФИО как в паспорте')

    else:
        await message.answer(
            f'Извините, но я не знаю такую страну, попробуйте написать иначе {random.choice(config.bad_reaction)}')
        return


@dp.message_handler(state=RegStates.wait_fullname)
async def fullname(message: types.message, state: FSMContext):
    for _ in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', "'", '"', '@', '\\', '|', '/', '!', '#', '$', '%', '^',
              '&', '*', '_', '=', '+', '?', '>', ',', '.']:
        if _ in message.text.lower():
            message.answer(f'Некорректное ФИО, попробуйте еще раз {random.choice(config.incorrect_reaction)}')
            return

    await state.update_data(fullname=message.text)
    await RegStates.next()
    await message.answer('Введите номер телефона')


@dp.message_handler(state=RegStates.wait_number)
async def number(message: types.message, state: FSMContext):
    global test_data
    if test_data and str(message.text) in test_data:
        await message.answer(f'Извините, но вы уже давали свои данные {random.choice(config.lying_reaction)}', reply_markup=main_buttons(2))
        await state.finish()
        await deleter(message.message_id, message.chat.id)
        return

    if 11 >= len(str(message.text)) >= 13:
        await message.answer(f'Некорректный номер телефона, возможно вы ошиблись {random.choice(config.incorrect_reaction)}')
        return

    for _ in str(message.text):
        if _ not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+']:
            await message.answer(
                f'Некорректный номер телефона, возможно вы ошиблись {random.choice(config.incorrect_reaction)}')
            return

    await state.update_data(number=message.text)
    await RegStates.next()
    await message.answer('Введите полный адрес прописки как в паспорте')


@dp.message_handler(state=RegStates.wait_address)
async def address(message: types.message, state: FSMContext):
    await state.update_data(address=str(message.text))
    await RegStates.next()
    await message.answer('Введите свой почтовый индекс (можно посмотреть в интернете, привязан к улице)')


@dp.message_handler(state=RegStates.wait_index)
async def index(message: types.message, state: FSMContext):
    await state.update_data(index=str(message.text))
    await RegStates.next()

    await message.answer('🎉')
    await deleter(message.message_id, message.chat.id)
    await message.answer('Поздравляю, информация сохранена!')
    await message.answer('Скоро с вами свяжется менеджер для прохождения верификации и выплаты 💰', reply_markup=main_buttons(2))

    data = await state.get_data()

    users = open('users.txt', 'a+', encoding='utf-8')
    if data['profile'] is not None:
        users.write(str(data['profile']) + '\n')
    users.write(str(data['number']) + '\n')
    users.close()
    print('Файл users.txt дополнен')

    users_data = open('users_data.txt', 'a+', encoding='utf-8')
    users_data.write(';'.join([str(_[1]) for _ in data.items()]) + '\n')
    users_data.close()
    print('Файл users_data.txt дополнен')


def main_buttons(rows: int) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=rows)
    button = [types.InlineKeyboardButton('FAQ', callback_data='FAQ'),
              types.InlineKeyboardButton('О coinlist', callback_data='coinlistinfo'),
              types.InlineKeyboardButton('РЕГИСТРАЦИЯ', callback_data='reg')]
    markup.add(*button)
    return markup


@dp.message_handler(Text(equals='хорошая работа олег', ignore_case=True))
async def secret_download(message: types.message):
    await message.answer_document(open('users_data.txt', 'rb'))


@dp.message_handler(commands='start')
async def main_menu(message: types.message):
    await message.answer(random.choice(config.welcome))
    await message.answer('Привет! Сәлем! Hello! Salom!', reply_markup=main_buttons(1))


@dp.callback_query_handler()
async def main_menu(call: types.callback_query):
    if call.message:
        if call.data == 'FAQ':
            await call.message.answer(config.FAQ_info, parse_mode=types.ParseMode.MARKDOWN_V2, reply_markup=main_buttons(2))

            await deleter(call.message.message_id, call.message.chat.id)

        elif call.data == 'coinlistinfo':
            await call.message.answer('конлист - тема, пушка', reply_markup=main_buttons(2))

            await deleter(call.message.message_id, call.message.chat.id)

        elif call.data == 'reg':
            await reg_start(call.message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
