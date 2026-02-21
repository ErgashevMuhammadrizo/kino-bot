import random
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from database import db
from utils.keyboards import (
    admin_main, admin_movie_menu, admin_series_menu, admin_channel_menu,
    channel_type_keyboard, cancel_keyboard, channel_post_button, main_menu
)
from config import ADMIN_IDS, ADMIN_PASSWORD, DB_CHANNEL_ID, MAIN_CHANNEL_ID

router = Router()


# ===== FSM STATES =====
class AdminAuth(StatesGroup):
    waiting_password = State()


class AddMovie(StatesGroup):
    name = State()
    photo = State()
    description = State()
    year = State()
    genre = State()
    video = State()


class AddSeries(StatesGroup):
    name = State()
    photo = State()
    description = State()
    year = State()
    genre = State()


class AddEpisode(StatesGroup):
    serial_code = State()
    season = State()
    episode_num = State()
    video = State()


class DeleteMovie(StatesGroup):
    code = State()


class DeleteSeries(StatesGroup):
    code = State()


class AddChannel(StatesGroup):
    channel_type = State()
    channel_id = State()
    title = State()
    link = State()


class DeleteChannel(StatesGroup):
    channel_id = State()


class Broadcast(StatesGroup):
    content = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def generate_unique_code() -> str:
    """Bazada mavjud bo'lmagan 4 xonali random kod yaratadi."""
    while True:
        code = str(random.randint(1000, 9999))
        existing_movie = await db.get_movie_by_code(code)
        existing_series = await db.get_series_by_code(code)
        if not existing_movie and not existing_series:
            return code


async def post_movie_to_main_channel(bot: Bot, data: dict, code: str, message: Message):
    """Kino qo'shilgandan keyin rasmiy kanalga post yuboradi."""
    if not MAIN_CHANNEL_ID:
        return

    me = await bot.get_me()

    caption = (
        f"🎬 <b>{data['name']}</b>\n\n"
        f"📅 <b>Yili:</b> {data['year']}\n"
        f"🎭 <b>Janr:</b> {data['genre']}\n\n"
        f"📝 {data['description']}\n\n"
        f"🤖 @{me.username}"
    )
    kb = channel_post_button(me.username, code)

    try:
        if data.get("thumb_file_id"):
            await bot.send_photo(
                chat_id=MAIN_CHANNEL_ID,
                photo=data["thumb_file_id"],
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=MAIN_CHANNEL_ID,
                text=caption,
                reply_markup=kb,
                parse_mode="HTML"
            )
    except Exception as e:
        await message.answer(f"⚠️ Rasmiy kanalga post tashlashda xato: {e}\n"
                             f"Bot kanalda admin ekanligini tekshiring!")


async def save_video_to_db_channel(bot: Bot, data: dict, code: str, message: Message):
    """Videoni DB kanaliga saqlaydi va message_id ni qaytaradi."""
    if not DB_CHANNEL_ID:
        return None

    try:
        video_msg = await bot.send_video(
            chat_id=DB_CHANNEL_ID,
            video=data["file_id"],
            caption=f"🎬 {data['name']} | #{code}"
        )
        return video_msg.message_id
    except Exception as e:
        await message.answer(f"⚠️ DB kanaliga video saqlashda xato: {e}")
        return None


# ===== ADMIN LOGIN =====
@router.message(Command("admin"))
async def admin_cmd(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Siz admin emassiz!")
        return

    if await db.is_admin_authenticated(message.from_user.id):
        await message.answer("✅ Admin paneliga xush kelibsiz!", reply_markup=admin_main())
        return

    await message.answer("🔐 Admin parolini kiriting:")
    await state.set_state(AdminAuth.waiting_password)


@router.message(AdminAuth.waiting_password)
async def admin_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await db.set_admin_auth(message.from_user.id, 1)
        await state.clear()
        await message.answer("✅ Muvaffaqiyatli kirdingiz!", reply_markup=admin_main())
    else:
        await message.answer("❌ Noto'g'ri parol!")


# ===== NAVIGATION =====
@router.message(F.text == "🎬 Kino")
async def admin_movie(message: Message):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("🎬 Kino bo'limi:", reply_markup=admin_movie_menu())


@router.message(F.text == "📺 Serial")
async def admin_series(message: Message):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("📺 Serial bo'limi:", reply_markup=admin_series_menu())


@router.message(F.text == "📢 Majburiy Obuna")
async def admin_channels(message: Message):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    channels = await db.get_all_channels()
    ch_text = ""
    if channels:
        for ch in channels:
            ch_type = "🔒 Yopiq" if ch["channel_type"] == "private" else "📢 Ochiq"
            ch_text += f"\n• {ch['title']} ({ch_type}) — <code>{ch['channel_id']}</code>"
    else:
        ch_text = "\nHozircha kanallar yo'q."

    await message.answer(
        f"📢 <b>Majburiy obuna bo'limi</b>{ch_text}",
        reply_markup=admin_channel_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "🔙 Admin panel")
async def back_to_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Admin panel:", reply_markup=admin_main())


@router.message(F.text == "🔙 Foydalanuvchi paneliga")
async def back_to_user(message: Message):
    await message.answer("Foydalanuvchi paneliga qaytdingiz.", reply_markup=main_menu())


# ===== ADD MOVIE =====
@router.message(F.text == "➕ Kino qo'shish")
async def add_movie_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("🎬 Kino nomini kiriting:", reply_markup=cancel_keyboard())
    await state.set_state(AddMovie.name)


@router.message(AddMovie.name)
async def add_movie_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📸 Rasm yuboring (poster):\n\n<i>O'tkazib yuborish uchun: o'tkazib yuborish</i>", parse_mode="HTML")
    await state.set_state(AddMovie.photo)


@router.message(AddMovie.photo, F.photo)
async def add_movie_photo(message: Message, state: FSMContext):
    await state.update_data(thumb_file_id=message.photo[-1].file_id)
    await message.answer("📝 Tavsif kiriting:")
    await state.set_state(AddMovie.description)


@router.message(AddMovie.photo, F.text == "o'tkazib yuborish")
async def skip_movie_photo(message: Message, state: FSMContext):
    await state.update_data(thumb_file_id=None)
    await message.answer("📝 Tavsif kiriting:")
    await state.set_state(AddMovie.description)


@router.message(AddMovie.description)
async def add_movie_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("📅 Yilini kiriting (masalan: 2023):")
    await state.set_state(AddMovie.year)


@router.message(AddMovie.year)
async def add_movie_year(message: Message, state: FSMContext):
    await state.update_data(year=message.text)
    await message.answer("🎭 Janrini kiriting (masalan: Action, Drama):")
    await state.set_state(AddMovie.genre)


@router.message(AddMovie.genre)
async def add_movie_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await message.answer("🎬 Video faylni yuboring:")
    await state.set_state(AddMovie.video)


@router.message(AddMovie.video, F.video)
async def add_movie_video(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(file_id=message.video.file_id)
    data = await state.get_data()

    # Random 4 xonali unikal kod yaratish
    code = await generate_unique_code()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    await db.add_movie(
        name=data["name"],
        description=data["description"],
        year=data["year"],
        genre=data["genre"],
        file_id=data["file_id"],
        thumb_file_id=data.get("thumb_file_id"),
        code=code,
        created_at=created_at
    )

    await state.clear()
    await message.answer(
        f"✅ Kino muvaffaqiyatli qo'shildi!\n"
        f"🔢 <b>Kino kodi: <code>{code}</code></b>",
        parse_mode="HTML"
    )

    # DB kanaliga videoni saqlash
    video_msg_id = await save_video_to_db_channel(bot, data, code, message)
    if video_msg_id:
        await db.update_movie_channel_msg(code, video_msg_id)

    # Rasmiy kanalga post yuborish
    await post_movie_to_main_channel(bot, data, code, message)


# ===== MOVIE LIST =====
@router.message(F.text == "📂 Kinolar ro'yxati")
async def movies_list(message: Message):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    movies = await db.get_all_movies()
    if not movies:
        await message.answer("Hozircha kinolar yo'q.")
        return

    text = "📂 <b>Kinolar ro'yxati:</b>\n\n"
    for m in movies[:30]:
        rating = round(m["total_rating"] / m["rating_count"], 1) if m["rating_count"] > 0 else 0
        text += f"🎬 {m['name']} | 🔢 <code>{m['code']}</code> | 👁 {m['views']} | ⭐ {rating}\n"

    await message.answer(text, parse_mode="HTML")


# ===== DELETE MOVIE =====
@router.message(F.text == "❌ Kino o'chirish")
async def delete_movie_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("O'chirmoqchi bo'lgan kino kodini kiriting:", reply_markup=cancel_keyboard())
    await state.set_state(DeleteMovie.code)


@router.message(DeleteMovie.code)
async def delete_movie_confirm(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = await db.get_movie_by_code(code)
    if not movie:
        await message.answer("❌ Bunday kodli kino topilmadi!")
        await state.clear()
        return

    await db.delete_movie(code)
    await state.clear()
    await message.answer(f"✅ <b>{movie['name']}</b> o'chirildi!", parse_mode="HTML")


# ===== ADD SERIES =====
@router.message(F.text == "➕ Serial qo'shish")
async def add_series_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("📺 Serial nomini kiriting:", reply_markup=cancel_keyboard())
    await state.set_state(AddSeries.name)


@router.message(AddSeries.name)
async def add_series_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📸 Rasm yuboring (poster):")
    await state.set_state(AddSeries.photo)


@router.message(AddSeries.photo, F.photo)
async def add_series_photo(message: Message, state: FSMContext):
    await state.update_data(thumb_file_id=message.photo[-1].file_id)
    await message.answer("📝 Tavsif kiriting:")
    await state.set_state(AddSeries.description)


@router.message(AddSeries.description)
async def add_series_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("📅 Yilini kiriting:")
    await state.set_state(AddSeries.year)


@router.message(AddSeries.year)
async def add_series_year(message: Message, state: FSMContext):
    await state.update_data(year=message.text)
    await message.answer("🎭 Janrini kiriting:")
    await state.set_state(AddSeries.genre)


@router.message(AddSeries.genre)
async def add_series_genre(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(genre=message.text)
    data = await state.get_data()

    # Random 4 xonali unikal kod
    code = await generate_unique_code()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    await db.add_series(
        name=data["name"],
        description=data["description"],
        code=code,
        year=data["year"],
        genre=data["genre"],
        thumb_file_id=data.get("thumb_file_id"),
        created_at=created_at
    )

    await state.clear()
    await message.answer(
        f"✅ Serial qo'shildi!\n"
        f"🔢 <b>Serial kodi: <code>{code}</code></b>",
        parse_mode="HTML"
    )

    # Rasmiy kanalga post
    if MAIN_CHANNEL_ID:
        me = await bot.get_me()
        caption = (
            f"📺 <b>{data['name']}</b>\n\n"
            f"📅 <b>Yili:</b> {data['year']}\n"
            f"🎭 <b>Janr:</b> {data['genre']}\n\n"
            f"📝 {data['description']}\n\n"
            f"🤖 @{me.username}"
        )
        from utils.keyboards import channel_post_button
        kb = channel_post_button(me.username, code)
        try:
            if data.get("thumb_file_id"):
                await bot.send_photo(MAIN_CHANNEL_ID, photo=data["thumb_file_id"], caption=caption, reply_markup=kb, parse_mode="HTML")
            else:
                await bot.send_message(MAIN_CHANNEL_ID, text=caption, reply_markup=kb, parse_mode="HTML")
        except Exception as e:
            await message.answer(f"⚠️ Rasmiy kanalga post tashlashda xato: {e}")


# ===== SERIES LIST =====
@router.message(F.text == "📂 Seriallar ro'yxati")
async def series_list(message: Message):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    series = await db.get_all_series()
    if not series:
        await message.answer("Hozircha seriallar yo'q.")
        return

    text = "📂 <b>Seriallar ro'yxati:</b>\n\n"
    for s in series[:30]:
        text += f"📺 {s['name']} | 🔢 <code>{s['code']}</code>\n"

    await message.answer(text, parse_mode="HTML")


# ===== DELETE SERIES =====
@router.message(F.text == "❌ Serial o'chirish")
async def delete_series_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("O'chirmoqchi bo'lgan serial kodini kiriting:", reply_markup=cancel_keyboard())
    await state.set_state(DeleteSeries.code)


@router.message(DeleteSeries.code)
async def delete_series_confirm(message: Message, state: FSMContext):
    code = message.text.strip()
    series = await db.get_series_by_code(code)
    if not series:
        await message.answer("❌ Bunday kodli serial topilmadi!")
        await state.clear()
        return
    await db.delete_series(code)
    await state.clear()
    await message.answer(f"✅ <b>{series['name']}</b> o'chirildi!", parse_mode="HTML")


# ===== ADD EPISODE =====
@router.message(F.text == "➕ Qism qo'shish")
async def add_episode_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("Serial kodini kiriting:", reply_markup=cancel_keyboard())
    await state.set_state(AddEpisode.serial_code)


@router.message(AddEpisode.serial_code)
async def add_episode_serial(message: Message, state: FSMContext):
    series = await db.get_series_by_code(message.text.strip())
    if not series:
        await message.answer("❌ Serial topilmadi! Qaytadan kiring:")
        return
    await state.update_data(serial_id=series["id"])
    await message.answer("Sezon raqamini kiriting (masalan: 1):")
    await state.set_state(AddEpisode.season)


@router.message(AddEpisode.season)
async def add_episode_season(message: Message, state: FSMContext):
    try:
        await state.update_data(season=int(message.text))
        await message.answer("Qism raqamini kiriting (masalan: 1):")
        await state.set_state(AddEpisode.episode_num)
    except ValueError:
        await message.answer("❌ Raqam kiriting!")


@router.message(AddEpisode.episode_num)
async def add_episode_num(message: Message, state: FSMContext):
    try:
        await state.update_data(episode_num=int(message.text))
        await message.answer("🎬 Video faylni yuboring:")
        await state.set_state(AddEpisode.video)
    except ValueError:
        await message.answer("❌ Raqam kiriting!")


@router.message(AddEpisode.video, F.video)
async def add_episode_video(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_episode(data["serial_id"], data["season"], data["episode_num"], message.video.file_id)
    await state.clear()
    await message.answer(
        f"✅ {data['season']}-Sezon {data['episode_num']}-Qism muvaffaqiyatli qo'shildi!"
    )


# ===== CHANNELS =====
@router.message(F.text == "➕ Kanal qo'shish")
async def add_channel_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer(
        "Kanal turini tanlang:\n\n"
        "📢 <b>Ochiq kanal</b> — oddiy obuna tekshiriladi\n"
        "🔒 <b>Yopiq kanal</b> — foydalanuvchi kanal linki orqali <b>so'rov yuborishi</b> va admin tasdiqlashi kerak. "
        "Bot kanalda admin bo'lishi shart!",
        reply_markup=channel_type_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AddChannel.channel_type)


@router.callback_query(F.data.startswith("chtype:"))
async def channel_type_selected(callback: CallbackQuery, state: FSMContext):
    ch_type = callback.data.split(":")[1]
    await state.update_data(channel_type=ch_type)

    if ch_type == "private":
        info = (
            "⚠️ <b>Yopiq kanal uchun muhim:</b>\n\n"
            "1. Botni kanalga <b>admin</b> qiling\n"
            "2. Kanal ID kiriting (masalan: <code>-100xxxxxxxxxx</code>)\n\n"
            "Kanal ID kiriting:"
        )
    else:
        info = "Kanal ID kiriting (masalan: @mychannel yoki <code>-100xxxxxxxxxx</code>):"

    await callback.message.edit_text(info, parse_mode="HTML")
    await state.set_state(AddChannel.channel_id)


@router.message(AddChannel.channel_id)
async def add_channel_id(message: Message, state: FSMContext, bot: Bot):
    channel_id = message.text.strip()

    # Kanal tekshirish
    try:
        chat = await bot.get_chat(channel_id)
        data = await state.get_data()

        if data.get("channel_type") == "private":
            # Bot admin ekanligini tekshirish
            bot_member = await bot.get_chat_member(chat_id=channel_id, user_id=(await bot.get_me()).id)
            from aiogram.enums import ChatMemberStatus
            if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                await message.answer(
                    "⚠️ <b>Diqqat!</b> Bot bu kanalda admin emas!\n"
                    "Bot adminlar ro'yxatiga qo'shing va qaytadan kiriting.",
                    parse_mode="HTML"
                )
                return

        await state.update_data(channel_id=channel_id, detected_title=chat.title)
        await message.answer(f"✅ Kanal topildi: <b>{chat.title}</b>\n\nKanal nomini kiriting (tugmada ko'rinadi):", parse_mode="HTML")
        await state.set_state(AddChannel.title)
    except Exception as e:
        await message.answer(
            f"❌ Kanal topilmadi yoki bot kanalga qo'shilmagan!\n"
            f"Xato: {e}\n\n"
            f"Qaytadan kiriting:",
            parse_mode="HTML"
        )


@router.message(AddChannel.title)
async def add_channel_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Kanal linkini kiriting (https://t.me/...):")
    await state.set_state(AddChannel.link)


@router.message(AddChannel.link)
async def add_channel_link(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_type = data["channel_type"]
    await db.add_channel(data["channel_id"], data["title"], channel_type, message.text.strip())
    await state.clear()

    type_text = "🔒 Yopiq (so'rov bilan)" if channel_type == "private" else "📢 Ochiq"
    await message.answer(
        f"✅ Kanal qo'shildi!\n"
        f"📛 Nomi: <b>{data['title']}</b>\n"
        f"🔖 Turi: {type_text}",
        parse_mode="HTML"
    )


@router.message(F.text == "📂 Kanallar ro'yxati")
async def channels_list(message: Message):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    channels = await db.get_all_channels()
    if not channels:
        await message.answer("Kanallar yo'q.")
        return
    text = "📢 <b>Majburiy obuna kanallari:</b>\n\n"
    for ch in channels:
        ch_type = "🔒 Yopiq" if ch["channel_type"] == "private" else "📢 Ochiq"
        text += f"• <b>{ch['title']}</b> ({ch_type})\n  ID: <code>{ch['channel_id']}</code>\n"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "❌ Kanal o'chirish")
async def delete_channel_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("O'chirmoqchi bo'lgan kanal ID kiriting:", reply_markup=cancel_keyboard())
    await state.set_state(DeleteChannel.channel_id)


@router.message(DeleteChannel.channel_id)
async def delete_channel_confirm(message: Message, state: FSMContext):
    await db.delete_channel(message.text.strip())
    await state.clear()
    await message.answer("✅ Kanal o'chirildi!")


# ===== STATISTICS =====
@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    stats = await db.get_stats()
    top = stats["top_movie"]
    top_text = f"{top[0]} ({top[1]} ko'rilgan)" if top else "Yo'q"

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b> {stats['users']:,}\n"
        f"🎬 <b>Kinolar:</b> {stats['movies']:,}\n"
        f"📺 <b>Seriallar:</b> {stats['series']:,}\n"
        f"⭐ <b>Baholar soni:</b> {stats['ratings']:,}\n"
        f"🔥 <b>Eng ko'rilgan kino:</b> {top_text}"
    )
    await message.answer(text, parse_mode="HTML")


# ===== BROADCAST =====
@router.message(F.text == "💰 Reklama")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id) or not await db.is_admin_authenticated(message.from_user.id):
        return
    await message.answer("📢 Yubormoqchi bo'lgan xabar yoki rasmni yuboring:", reply_markup=cancel_keyboard())
    await state.set_state(Broadcast.content)


@router.message(Broadcast.content)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = await db.get_all_users()
    sent = 0
    failed = 0

    await message.answer(f"📤 {len(users)} ta userga yuborilmoqda...")

    for user in users:
        try:
            await message.copy_to(chat_id=user[0])
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"✅ Reklama yakunlandi!\n✅ Yuborildi: {sent}\n❌ Xato: {failed}")


# ===== CANCEL =====
@router.callback_query(F.data == "cancel_admin")
async def cancel_admin_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    if is_admin(callback.from_user.id):
        await callback.message.answer("Admin panel:", reply_markup=admin_main())
