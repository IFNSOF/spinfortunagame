import json, random, time
from aiogram import Bot, Dispatcher, executor, types

TOKEN = "8204880484:AAHZKpUgPBl_hJj_ZQ8HaEczn1dg6njuxZo"
ADMIN_USERNAME = "winikson"
DATA_FILE = "data.json"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# === Функции для работы с базой ===
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "channels": ["@canal1", "@canal2"], "total_users": 0, "start_date": time.strftime("%Y-%m-%d")}

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

# === Меню ===
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎰 Играть", "👤 Профиль").add("💸 Ежечасовый бонус", "📊 Статистика").add("🛠 Тех. поддержка")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💰 Выдать деньги").add("➕ Добавить канал", "➖ Удалить канал").add("⬅️ В меню")
    return kb

# === Команды ===
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

# === Игра ===
@dp.message_handler(lambda m: m.text == "🎰 Играть")
async def play(msg: types.Message):
    await msg.answer("💰 Введите сумму ставки:")

    @dp.message_handler(lambda m: m.text.isdigit())
    async def bet_handler(bet_msg: types.Message):
        user_id = str(bet_msg.from_user.id)
        bet = int(bet_msg.text)
        user = data["users"][user_id]

        if user["balance"] < bet:
            await bet_msg.answer("❌ Недостаточно средств!", reply_markup=main_menu())
            return

        user["balance"] -= bet
        slots = ["🍒", "🍋", "🍇", "💎", "7️⃣"]
        result = [random.choice(slots) for _ in range(3)]
        win = random.random() < 0.6

        if win:
            prize = bet * 2
            user["balance"] += prize
            text = f"{' '.join(result)}\n🎉 Победа! +{prize} Wn"
        else:
            text = f"{' '.join(result)}\n😢 Проигрыш!"

        save_data(data)
        await bet_msg.answer(text, reply_markup=main_menu())

# === Профиль ===
@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def profile(msg: types.Message):
    u = data["users"][str(msg.from_user.id)]
    await msg.answer(f"👤 Ник: @{u['name']}\n💰 Баланс: {u['balance']} Wn", reply_markup=main_menu())

# === Ежечасовый бонус ===
@dp.message_handler(lambda m: m.text == "💸 Ежечасовый бонус")
async def bonus(msg: types.Message):
    user_id = str(msg.from_user.id)
    user = data["users"][user_id]
    now = time.time()

    if now - user["last_bonus"] >= 3600:
        user["balance"] += 500
        user["last_bonus"] = now
        save_data(data)
        await msg.answer("✅ Вы получили 500 Wn!", reply_markup=main_menu())
    else:
        remain = int(3600 - (now - user["last_bonus"])) // 60
        await msg.answer(f"⏳ Бонус можно получить через {remain} мин.", reply_markup=main_menu())

# === Статистика ===
@dp.message_handler(lambda m: m.text == "📊 Статистика")
async def stats(msg: types.Message):
    await msg.answer(
        f"📅 Дата старта: {data['start_date']}\n"
        f"👑 Владелец: @{ADMIN_USERNAME}\n"
        f"👥 Всего пользователей: {data['total_users']}",
        reply_markup=main_menu()
    )

# === Техподдержка ===
@dp.message_handler(lambda m: m.text == "🛠 Тех. поддержка")
async def support(msg: types.Message):
    await msg.answer("✉️ Опиши проблему одним сообщением:")

    @dp.message_handler(lambda m: True)
    async def send_support(rep: types.Message):
        if rep.from_user.username == ADMIN_USERNAME:
            return
        kb = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Ответить", callback_data=f"reply_{rep.from_user.id}")
        )
        await msg.answer("✅ Сообщение отправлено админу!")
        await bot.send_message(
            msg.from_user.id,
            f"🆘 Сообщение от @{rep.from_user.username}:\n{rep.text}",
            reply_markup=kb
        )

# === Админ панель ===
@dp.message_handler(lambda m: m.from_user.username == ADMIN_USERNAME and m.text.lower() == "/admin")
async def admin_panel(msg: types.Message):
    await msg.answer("🔐 Админ-панель", reply_markup=admin_menu())

@dp.message_handler(lambda m: m.from_user.username == ADMIN_USERNAME and m.text == "💰 Выдать деньги")
async def give_money(msg: types.Message):
    await msg.answer("💸 Введи ID и сумму через пробел:")

    @dp.message_handler(lambda m: True)
    async def gm(m2: types.Message):
        try:
            uid, amount = m2.text.split()
            data["users"][uid]["balance"] += int(amount)
            save_data(data)
            await m2.answer("✅ Готово!", reply_markup=admin_menu())
        except:
            await m2.answer("Ошибка ввода!")

@dp.message_handler(lambda m: m.from_user.username == ADMIN_USERNAME and m.text == "➕ Добавить канал")
async def add_channel(msg: types.Message):
    await msg.answer("Введите @username канала:")
    @dp.message_handler(lambda m: m.text.startswith("@"))
    async def add(m2: types.Message):
        data["channels"].append(m2.text)
        save_data(data)
        await m2.answer(f"✅ Канал {m2.text} добавлен.", reply_markup=admin_menu())

@dp.message_handler(lambda m: m.from_user.username == ADMIN_USERNAME and m.text == "➖ Удалить канал")
async def del_channel(msg: types.Message):
    await msg.answer("Введите @username канала для удаления:")
    @dp.message_handler(lambda m: m.text.startswith("@"))
    async def delete(m2: types.Message):
        if m2.text in data["channels"]:
            data["channels"].remove(m2.text)
            save_data(data)
            await m2.answer(f"🗑 Удален {m2.text}", reply_markup=admin_menu())
        else:
            await m2.answer("Не найдено!", reply_markup=admin_menu())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

