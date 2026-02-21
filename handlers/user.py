from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database import db
from utils.keyboards import (
    main_menu, movie_actions, rating_keyboard, back_btn,
    series_seasons_keyboard, episodes_keyboard, subscribe_keyboard, cancel_keyboard
)
from utils.subscription import check_subscription
from config import DB_CHANNEL_ID

router = Router()


async def get_content_by_code(code: str):
    """Search movie or series by code"""
    movie = await db.get_movie_by_code(code)
    if movie:
        return ("movie", movie)
    series = await db.get_series_by_code(code)
    if series:
        return ("series", series)
    return (None, None)


async def show_subscribe_panel(message_or_callback, channels, bot_username, code, bot: Bot):
    """Majburiy obuna panelini ko'rsatadi."""
    kb = subscribe_keyboard(channels, bot_username, code)

    # Yopiq kanallar uchun maxsus matn
    has_private = any(ch["channel_type"] == "private" for ch in channels)

    if has_private:
        text = (
            "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
            "🔒 <i>Yopiq kanallar uchun: tugmani bosib so'rov yuboring va admin tasdiqlashini kuting.</i>"
        )
    else:
        text = "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>"

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        try:
            await message_or_callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await message_or_callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user = message.from_user
    await db.add_user(user.id, user.username or "", user.full_name)

    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        await handle_content_code(message, code, bot)
        return

    await message.answer(
        "🎬 <b>Assalomu alaykum!</b>\n\n"
        "O'zingizga kerakli kino, serial yoki anime kodini kiriting.\n"
        "Masalan: <code>1025</code>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


async def handle_content_code(message: Message, code: str, bot: Bot):
    channels = await db.get_all_channels()

    # Obunani tekshirish
    if channels:
        is_subscribed = await check_subscription(bot, message.from_user.id, channels)
        if not is_subscribed:
            me = await bot.get_me()
            await show_subscribe_panel(message, channels, me.username, code, bot)
            return

    content_type, content = await get_content_by_code(code)

    if not content:
        await message.answer("❌ <b>Bunday kodli kino yoki serial topilmadi!</b>", parse_mode="HTML")
        return

    if content_type == "movie":
        await show_movie(message, content, bot)
    elif content_type == "series":
        await show_series(message, content, bot)


async def show_movie(message: Message, movie, bot: Bot):
    rating = round(movie["total_rating"] / movie["rating_count"], 1) if movie["rating_count"] > 0 else 0

    caption = (
        f"🎬 <b>Nomi:</b> {movie['name']}\n"
        f"📅 <b>Yili:</b> {movie['year']}\n"
        f"🎭 <b>Janr:</b> {movie['genre']}\n"
        f"⭐ <b>Reyting:</b> {rating} / 10\n"
        f"📝 <b>Tavsif:</b> {movie['description']}\n"
        f"📊 <b>Ko'rishlar:</b> {movie['views']}"
    )

    await db.increment_movie_views(movie["code"])
    await db.increment_watched(message.from_user.id)

    kb = movie_actions(movie["code"], movie["id"])

    if movie["thumb_file_id"]:
        await message.answer_photo(
            photo=movie["thumb_file_id"],
            caption=caption,
            reply_markup=kb,
            parse_mode="HTML"
        )
    else:
        await message.answer(caption, reply_markup=kb, parse_mode="HTML")


async def show_series(message: Message, series, bot: Bot):
    caption = (
        f"📺 <b>Nomi:</b> {series['name']}\n"
        f"📅 <b>Yili:</b> {series['year']}\n"
        f"🎭 <b>Janr:</b> {series['genre']}\n"
        f"📝 <b>Tavsif:</b> {series['description']}"
    )

    seasons = await db.get_episodes(series["id"])
    kb = series_seasons_keyboard(series["id"], seasons)

    if series["thumb_file_id"]:
        await message.answer_photo(
            photo=series["thumb_file_id"],
            caption=caption,
            reply_markup=kb,
            parse_mode="HTML"
        )
    else:
        await message.answer(caption, reply_markup=kb, parse_mode="HTML")


@router.message(F.text == "👤 Profil")
async def profile_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Siz hali ro'yxatdan o'tmagansiz.")
        return

    text = (
        f"👤 <b>Profil</b>\n\n"
        f"🆔 <b>ID:</b> {user['user_id']}\n"
        f"📅 <b>Ro'yxatdan o'tgan:</b> {user['join_date']}\n"
        f"🎬 <b>Ko'rgan kinolar:</b> {user['watched_count']}\n"
        f"⭐ <b>Qoldirgan baholar:</b> {user['rating_count']}"
    )
    await message.answer(text, reply_markup=back_btn(), parse_mode="HTML")


@router.message(F.text == "📞 Yordam")
async def help_handler(message: Message):
    text = (
        "📞 <b>Yordam</b>\n\n"
        "Botdan foydalanish:\n\n"
        "1️⃣ Kino kodini yuboring\n"
        "2️⃣ Majburiy obunadan o'ting\n"
        "3️⃣ Tomosha qiling!\n\n"
        "Har qanday muammo uchun admin bilan bog'laning."
    )
    await message.answer(text, reply_markup=back_btn(), parse_mode="HTML")


@router.message(F.text == "⭐ Reyting")
async def top_handler(message: Message):
    movies = await db.get_top_movies(10)
    if not movies:
        await message.answer("Hozircha kinolar mavjud emas.")
        return

    text = "🔥 <b>Top 10 kinolar (ko'rishlar bo'yicha):</b>\n\n"
    for i, m in enumerate(movies, 1):
        rating = round(m["total_rating"] / m["rating_count"], 1) if m["rating_count"] > 0 else 0
        text += f"{i}. 🎬 {m['name']} — 👁 {m['views']} | ⭐ {rating}\n"

    await message.answer(text, reply_markup=back_btn(), parse_mode="HTML")


@router.message(F.text.regexp(r'^\d+$'))
async def code_handler(message: Message, bot: Bot):
    await handle_content_code(message, message.text.strip(), bot)


# ===== CALLBACKS =====

@router.callback_query(F.data.startswith("check_sub:"))
async def check_subscription_callback(callback: CallbackQuery, bot: Bot):
    code = callback.data.split(":")[1]
    channels = await db.get_all_channels()
    is_subscribed = await check_subscription(bot, callback.from_user.id, channels)

    if not is_subscribed:
        # Qaysi kanallarga obuna bo'lmaganini ko'rsatish
        not_subscribed = []
        for ch in channels:
            from utils.subscription import check_single_channel
            ok = await check_single_channel(bot, callback.from_user.id, ch["channel_id"])
            if not ok:
                not_subscribed.append(ch["title"])

        names = ", ".join(not_subscribed) if not_subscribed else "ba'zi kanallar"
        await callback.answer(
            f"❌ Siz hali obuna bo'lmagansiz: {names}",
            show_alert=True
        )
        return

    content_type, content = await get_content_by_code(code)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if content_type == "movie":
        await show_movie(callback.message, content, bot)
    elif content_type == "series":
        await show_series(callback.message, content, bot)
    else:
        await callback.message.answer("❌ Kino topilmadi.")


@router.callback_query(F.data.startswith("watch_movie:"))
async def watch_movie_callback(callback: CallbackQuery, bot: Bot):
    code = callback.data.split(":")[1]
    movie = await db.get_movie_by_code(code)
    if not movie:
        await callback.answer("Kino topilmadi!", show_alert=True)
        return

    await callback.answer("📥 Kino yuklanmoqda...")

    if movie["channel_message_id"] and DB_CHANNEL_ID:
        try:
            await bot.copy_message(
                chat_id=callback.from_user.id,
                from_chat_id=DB_CHANNEL_ID,
                message_id=movie["channel_message_id"]
            )
        except Exception:
            await bot.send_video(callback.from_user.id, video=movie["file_id"], caption=f"🎬 {movie['name']}")
    else:
        await bot.send_video(callback.from_user.id, video=movie["file_id"], caption=f"🎬 {movie['name']}")


@router.callback_query(F.data.startswith("rate_movie:"))
async def rate_movie_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    movie_id = parts[1]
    code = parts[2]

    already_rated = await db.has_rated(callback.from_user.id, int(movie_id), "movie")
    if already_rated:
        await callback.answer("⭐ Siz bu kinoni allaqachon baholagansiz!", show_alert=True)
        return

    kb = rating_keyboard(movie_id, code)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("give_rating:"))
async def give_rating_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    content_type = parts[1]
    content_id = int(parts[2])
    code = parts[3]
    rating = int(parts[4])

    success = await db.add_rating(callback.from_user.id, content_id, content_type, rating)
    if not success:
        await callback.answer("⭐ Siz allaqachon baholagansiz!", show_alert=True)
        return

    if content_type == "movie":
        await db.update_movie_rating(code, rating)

    import aiosqlite
    async with aiosqlite.connect("kinobot.db") as db_conn:
        await db_conn.execute(
            "UPDATE users SET rating_count = rating_count + 1 WHERE user_id=?",
            (callback.from_user.id,)
        )
        await db_conn.commit()

    await callback.answer(f"✅ Sizning bahoyingiz: {rating}/10 — rahmat!", show_alert=True)
    kb = movie_actions(code, content_id)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("season:"))
async def season_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    serial_id = int(parts[1])
    season = int(parts[2])

    episodes = await db.get_episodes(serial_id, season)
    if not episodes:
        await callback.answer("Bu sezonda qismlar topilmadi.", show_alert=True)
        return

    kb = episodes_keyboard(serial_id, season, episodes)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("back_seasons:"))
async def back_seasons_callback(callback: CallbackQuery):
    serial_id = int(callback.data.split(":")[1])
    seasons = await db.get_episodes(serial_id)
    kb = series_seasons_keyboard(serial_id, seasons)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@router.callback_query(F.data.startswith("episode:"))
async def episode_callback(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    serial_id = int(parts[1])
    season = int(parts[2])
    episode_num = int(parts[3])

    episodes = await db.get_episodes(serial_id, season)
    target = None
    for ep in episodes:
        if ep["episode"] == episode_num:
            target = ep
            break

    if not target:
        await callback.answer("Qism topilmadi!", show_alert=True)
        return

    await callback.answer("📥 Qism yuklanmoqda...")
    await bot.send_video(
        callback.from_user.id,
        video=target["file_id"],
        caption=f"📺 {season}-Sezon | {episode_num}-Qism"
    )


@router.callback_query(F.data == "back_home")
async def back_home_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "🎬 <b>Assalomu alaykum!</b>\n\nKino kodini kiriting yoki tugmalardan foydalaning.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("back_movie:"))
async def back_movie_callback(callback: CallbackQuery, bot: Bot):
    code = callback.data.split(":")[1]
    movie = await db.get_movie_by_code(code)
    if not movie:
        return
    rating = round(movie["total_rating"] / movie["rating_count"], 1) if movie["rating_count"] > 0 else 0
    caption = (
        f"🎬 <b>Nomi:</b> {movie['name']}\n"
        f"📅 <b>Yili:</b> {movie['year']}\n"
        f"🎭 <b>Janr:</b> {movie['genre']}\n"
        f"⭐ <b>Reyting:</b> {rating} / 10\n"
        f"📝 <b>Tavsif:</b> {movie['description']}\n"
        f"📊 <b>Ko'rishlar:</b> {movie['views']}"
    )
    kb = movie_actions(movie["code"], movie["id"])
    try:
        await callback.message.edit_caption(caption=caption, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
