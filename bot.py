import json, random, time, asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiohttp import web

TOKEN = "8499397849:AAGQWQF6O0SCjNP9nMuld0loFTmK47c7yZk"  # вставь сюда токен своего бота
ADMIN_USERNAME = "winikson"
DATA_FILE = "data.json"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# === Работа с JSON базой ===
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "users": {},
            "channels": ["@canal1", "@canal2"],
            "total_users": 0,
            "start_date": time.strftime("%Y-%m-%d")
        }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

# === Проверка подписки ===
async def check_sub(user_id):
    for ch in data["channels"]:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True

# === Главное меню ===
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎰 Играть", "👤 Профиль")
    kb.add("💸 Ежечасовый бонус", "📊 Статистика")
    kb.add("🛠 Тех. поддержка")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💰 Выдать деньги")
    kb.add("➕ Добавить канал", "➖ Удалить канал")
    kb.add("⬅️ В меню")
    return kb

# === /start ===
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    user_id = str(msg.from_user.id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "name": msg.from_user.username or msg.from_user.first_name,
            "balance": 1000,
            "last_bonus": 0
        }
        data["total_users"] += 1
        save_data(data)

    if not await check_sub(msg.from_user.id):
        chs = "\n".join(data["channels"])
        await msg.answer(f"📢 Для использования бота подпишись на каналы:\n{chs}")
        return

    await msg.answer("🎰 Добро пожаловать в Spin Fortuna!", reply_markup=main_menu())

# === Играть ===
@dp.message_handler(lambda m: m.text == "🎰 Играть")
async def play(msg: types.Message):
    ask = await msg.answer("💰 Введите сумму ставки:")

    @dp.message_handler(lambda m: m.text.isdigit())
    async def bet(bet_msg: types.Message):
        try:
            await bot.delete_message(msg.chat.id, ask.message_id)
            await bot.delete_message(bet_msg.chat.id, bet_msg.message_id)
        except: pass

        user = data["users"][str(bet_msg.from_user.id)]
        bet = int(bet_msg.text)
        if user["balance"] < bet:
            m = await bet_msg.answer("❌ Недостаточно средств!", reply_markup=main_menu())
            await asyncio.sleep(3)
            await m.delete()
            return

        user["balance"] -= bet
        res = [random.choice(["🍒", "🍋", "🍇", "💎", "7️⃣"]) for _ in range(3)]
        if random.random() < 0.6:
            prize = bet * 2
            user["balance"] += prize
            text = f"{' '.join(res)}\n🎉 Победа! +{prize} Wn"
        else:
            text = f"{' '.join(res)}\n😢 Проигрыш!"
        save_data(data)

        m = await bet_msg.answer(text, reply_markup=main_menu())
        await asyncio.sleep(8)
        try:
            await bot.delete_message(bet_msg.chat.id, m.message_id)
        except: pass

# === Профиль ===
@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def profile(msg: types.Message):
    u = data["users"][str(msg.from_user.id)]
    m = await msg.answer(f"👤 Ник: @{u['name']}\n💰 Баланс: {u['balance']} Wn", reply_markup=main_menu())
    await asyncio.sleep(8)
    try:
        await bot.delete_message(msg.chat.id, m.message_id)
        await bot.delete_message(msg.chat.id, msg.message_id)
    except: pass

# === Бонус ===
@dp.message_handler(lambda m: m.text == "💸 Ежечасовый бонус")
async def bonus(msg: types.Message):
    u = data["users"][str(msg.from_user.id)]
    now = time.time()
    if now - u["last_bonus"] >= 3600:
        u["balance"] += 500
        u["last_bonus"] = now
        save_data(data)
        text = "✅ Вы получили 500 Wn!"
    else:
        remain = int(3600 - (now - u["last_bonus"])) // 60
        text = f"⏳ Следующий бонус через {remain} мин."
    m = await msg.answer(text, reply_markup=main_menu())
    await asyncio.sleep(8)
    try:
        await bot.delete_message(msg.chat.id, m.message_id)
        await bot.delete_message(msg.chat.id, msg.message_id)
    except: pass

# === Статистика ===
@dp.message_handler(lambda m: m.text == "📊 Статистика")
async def stats(msg: types.Message):
    m = await msg.answer(
        f"📅 Дата старта: {data['start_date']}\n"
        f"👑 Владелец: @{ADMIN_USERNAME}\n"
        f"👥 Всего пользователей: {data['total_users']}",
        reply_markup=main_menu()
    )
    await asyncio.sleep(8)
    try:
        await bot.delete_message(msg.chat.id, m.message_id)
        await bot.delete_message(msg.chat.id, msg.message_id)
    except: pass

# === Техподдержка ===
@dp.message_handler(lambda m: m.text == "🛠 Тех. поддержка")
async def support(msg: types.Message):
    ask = await msg.answer("✉️ Опиши проблему одним сообщением:")
    await asyncio.sleep(10)
    try:
        await bot.delete_message(msg.chat.id, ask.message_id)
        await bot.delete_message(msg.chat.id, msg.message_id)
    except: pass

# === Админ панель ===
@dp.message_handler(lambda m: m.from_user.username == ADMIN_USERNAME and m.text.lower() == "/admin")
async def admin_panel(msg: types.Message):
    await msg.answer("🔐 Админ-панель", reply_markup=admin_menu())

@dp.message_handler(lambda m: m.from_user.username == ADMIN_USERNAME and m.text == "💰 Выдать деньги")
async def give_money(msg: types.Message):
    ask = await msg.answer("💸 Введи ID и сумму через пробел:")

    @dp.message_handler(lambda m: True)
    async def gm(m2: types.Message):
        try:
            await bot.delete_message(m2.chat.id, m2.message_id)
            await bot.delete_message(msg.chat.id, ask.message_id)
        except: pass
        try:
            uid, amt = m2.text.split()
            data["users"][uid]["balance"] += int(amt)
            save_data(data)
            await m2.answer("✅ Готово!", reply_markup=admin_menu())
        except:
            await m2.answer("Ошибка!")

@dp.message_handler(lambda m: m.from_user.username == ADMIN_USERNAME and m.text == "➕ Добавить канал")
async def add_channel(msg: types.Message):
    ask = await msg.answer("Введите @username канала:")
    @dp.message_handler(lambda m: m.text.startswith("@"))
    async def add(m2: types.Message):
        data["channels"].append(m2.text)
        save_data(data)
        await m2.answer(f"✅ Добавлен {m2.text}", reply_markup=admin_menu())
        try:
            await bot.delete_message(m2.chat.id, m2.message_id)
            await bot.delete_message(msg.chat.id, ask.message_id)
        except: pass

@dp.message_handler(lambda m: m.from_user.username == ADMIN_USERNAME and m.text == "➖ Удалить канал")
async def del_channel(msg: types.Message):
    ask = await msg.answer("Введите @username канала для удаления:")
    @dp.message_handler(lambda m: m.text.startswith("@"))
    async def delete(m2: types.Message):
        if m2.text in data["channels"]:
            data["channels"].remove(m2.text)
            save_data(data)
            await m2.answer(f"🗑 Удален {m2.text}", reply_markup=admin_menu())
        else:
            await m2.answer("Не найдено!", reply_markup=admin_menu())
        try:
            await bot.delete_message(m2.chat.id, m2.message_id)
            await bot.delete_message(msg.chat.id, ask.message_id)
        except: pass

# === Пинг-сервер для Koyeb ===
async def ping(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/ping", ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8000)
    await site.start()

# === Запуск ===
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    executor.start_polling(dp, skip_updates=True, loop=loop)
