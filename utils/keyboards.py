from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Profil"), KeyboardButton(text="⭐ Reyting")],
            [KeyboardButton(text="📞 Yordam")],
        ],
        resize_keyboard=True
    )


def admin_main():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino"), KeyboardButton(text="📺 Serial")],
            [KeyboardButton(text="📢 Majburiy Obuna"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="💰 Reklama")],
            [KeyboardButton(text="🔙 Foydalanuvchi paneliga")],
        ],
        resize_keyboard=True
    )


def admin_movie_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kino qo'shish"), KeyboardButton(text="📂 Kinolar ro'yxati")],
            [KeyboardButton(text="❌ Kino o'chirish")],
            [KeyboardButton(text="🔙 Admin panel")],
        ],
        resize_keyboard=True
    )


def admin_series_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Serial qo'shish"), KeyboardButton(text="📂 Seriallar ro'yxati")],
            [KeyboardButton(text="❌ Serial o'chirish"), KeyboardButton(text="➕ Qism qo'shish")],
            [KeyboardButton(text="🔙 Admin panel")],
        ],
        resize_keyboard=True
    )


def admin_channel_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kanal qo'shish"), KeyboardButton(text="📂 Kanallar ro'yxati")],
            [KeyboardButton(text="❌ Kanal o'chirish")],
            [KeyboardButton(text="🔙 Admin panel")],
        ],
        resize_keyboard=True
    )


def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_admin")]
        ]
    )


def back_btn():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]
        ]
    )


def movie_actions(code: str, movie_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Tomosha qilish", callback_data=f"watch_movie:{code}")],
            [InlineKeyboardButton(text="⭐ Baholash", callback_data=f"rate_movie:{movie_id}:{code}")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")],
        ]
    )


def rating_keyboard(movie_id: str, code: str):
    buttons = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(
            text=str(i),
            callback_data=f"give_rating:movie:{movie_id}:{code}:{i}"
        ))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"back_movie:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def subscribe_keyboard(channels: list, bot_username: str, code: str):
    """
    Majburiy obuna klaviaturasi.
    Ochiq kanal: to'g'ridan-to'g'ri link.
    Yopiq kanal: kanal linki (join request uchun).
    """
    buttons = []
    for ch in channels:
        channel_type = ch["channel_type"]
        title = ch["title"]
        link = ch["link"]

        if channel_type == "private":
            # Yopiq kanal: so'rov yuborish uchun link
            buttons.append([
                InlineKeyboardButton(text=f"🔒 {title} — So'rov yuborish", url=link)
            ])
        else:
            # Ochiq kanal: oddiy obuna
            buttons.append([
                InlineKeyboardButton(text=f"📢 {title}", url=link)
            ])

    # Tekshirish tugmasi
    buttons.append([
        InlineKeyboardButton(text="✅ Obuna bo'ldim — Tekshirish", callback_data=f"check_sub:{code}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channel_post_button(bot_username: str, code: str):
    """Kanalga post uchun 'Tomosha qilish' tugmasi."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="▶️ Tomosha qilish",
                url=f"https://t.me/{bot_username}?start={code}"
            )]
        ]
    )


def channel_type_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Ochiq kanal", callback_data="chtype:open"),
                InlineKeyboardButton(text="🔒 Yopiq kanal", callback_data="chtype:private"),
            ]
        ]
    )


def series_seasons_keyboard(serial_id: int, seasons: list):
    buttons = []
    row = []
    for s in seasons:
        row.append(InlineKeyboardButton(
            text=f"{s['season']}-Sezon",
            callback_data=f"season:{serial_id}:{s['season']}"
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def episodes_keyboard(serial_id: int, season: int, episodes: list):
    buttons = []
    row = []
    for ep in episodes:
        row.append(InlineKeyboardButton(
            text=f"{ep['episode']}-Qism",
            callback_data=f"episode:{serial_id}:{season}:{ep['episode']}"
        ))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Sezonlar", callback_data=f"back_seasons:{serial_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
