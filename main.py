import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.bot import DefaultBotProperties
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"  # для локального тестирования
ADMIN_IDS = [7212288453]

channels_to_show = [
    ("https://t.me/+VYwk8CNxYRtkNTQy", "Канал 1"),
    ("https://t.me/+DKL9QMs_l8RkMzRi", "Канал 2"),
    ("https://t.me/+q73NJr1o6G81MGJi", "Канал 3")
]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
users_file = "users.json"

def load_users():
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_user(user_id):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"balance": 50, "confirmed": False}
        save_users(users)

def get_balance(user_id):
    users = load_users()
    return users.get(str(user_id), {}).get("balance", 0)

def update_balance(user_id, amount):
    users = load_users()
    users[str(user_id)]["balance"] += amount
    save_users(users)

def mark_confirmed(user_id):
    users = load_users()
    users[str(user_id)]["confirmed"] = True
    save_users(users)

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu(user_id):
    buttons = [
        InlineKeyboardButton(text="👛 Кошелек", callback_data="wallet"),
        InlineKeyboardButton(text="🍑 Подписки", callback_data="subscriptions"),
        InlineKeyboardButton(text="🔷 P2P", callback_data="p2p"),
        InlineKeyboardButton(text="📊 Биржа", callback_data="exchange"),
        InlineKeyboardButton(text="🦋 Чеки", callback_data="checks"),
        InlineKeyboardButton(text="📑 Счета", callback_data="bills"),
        InlineKeyboardButton(text="🪙 Crypto Pay", callback_data="crypto_pay"),
        InlineKeyboardButton(text="🏅 Конкурсы", callback_data="contests"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
    ]
    if is_admin(int(user_id)):
        buttons.append(InlineKeyboardButton(text="👑 Админ‑панель", callback_data="admin_panel"))
    inline = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=inline)

def wallet_menu():
    kb = [
        [
            InlineKeyboardButton(text="Пополнить", callback_data="wallet_deposit"),
            InlineKeyboardButton(text="Вывести", callback_data="wallet_withdraw"),
        ],
        [InlineKeyboardButton(text="Адресная книга", callback_data="wallet_address_book")],
        [InlineKeyboardButton(text="Комиссии и лимиты", callback_data="wallet_fees")],
        [InlineKeyboardButton(text="‹ Назад", callback_data="wallet_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    u = str(message.from_user.id)
    add_user(u)
    users = load_users()
    user = users.get(u)

    if user.get("confirmed"):
        await message.answer("✅ Аккаунт активен!", reply_markup=main_menu(u))
    else:
        kb = [[InlineKeyboardButton(text=name, url=link)] for link,name in channels_to_show]
        kb.append([InlineKeyboardButton(text="✅ Я подписался", callback_data="confirm_subs")])
        await message.answer("🎉 Вы получили 50$! Подпишитесь на каналы и нажмите кнопку:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query()
async def on_callback(callback: types.CallbackQuery):
    uid = str(callback.from_user.id)
    data = callback.data

    if data == "confirm_subs":
        udata = load_users().get(uid)
        if not udata["confirmed"]:
            update_balance(uid,60)
            mark_confirmed(uid)
            await callback.message.answer("🎉 Вы получили ещё 60$", reply_markup=main_menu(uid))
        else:
            await callback.message.answer("Уже получено")
        await callback.answer()

    elif data == "wallet":
        bal = get_balance(uid)
        await callback.message.answer(f"👜 Баланс: {bal:.2f} USDT", reply_markup=wallet_menu())
        await callback.answer()

    elif data.startswith("wallet_"):
        text = {
            "wallet_deposit": "💸 Пополнение пока недоступно",
            "wallet_withdraw": "🏦 Вывод доступен от 150 USDT",
            "wallet_address_book": "📒 Адресная книга пуста",
            "wallet_fees": "💼 Комиссия: 1 USDT, лимит: 5000 USDT/день",
            "wallet_back": f"🔙 Главное меню"
        }[data]
        kb = main_menu(uid) if data=="wallet_back" else None
        await callback.message.answer(text, reply_markup=kb)
        await callback.answer()

    elif data == "admin_panel":
        if is_admin(callback.from_user.id):
            total = len(load_users())
            await callback.message.answer(f"👑 Админпанель:\nВсего пользователей: {total}")
        else:
            await callback.answer("⛔ Нет доступа", show_alert=True)

    else:
        await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
