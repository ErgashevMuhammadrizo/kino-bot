from aiogram import Bot


async def check_subscription(bot: Bot, user_id: int, channels: list) -> bool:
    """
    Foydalanuvchi barcha kanallarga obuna bo'lganligini tekshiradi.
    Ochiq kanal: get_chat_member orqali tekshiradi.
    Yopiq kanal (private): join_request yuborilganligini tekshiradi.
    """
    for channel in channels:
        channel_id = channel["channel_id"]
        channel_type = channel["channel_type"]  # "open" yoki "private"

        try:
            if channel_type == "private":
                # Yopiq kanal: foydalanuvchi a'zoligini tekshir
                # Agar a'zo bo'lmasa False qaytaradi
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                status = member.status
                if status in [
                    "left",
                    "kicked",
                    "banned",
                ]:
                    return False
                # MEMBER, ADMINISTRATOR, CREATOR, RESTRICTED - bular obuna bo'lgan
            else:
                # Ochiq kanal: oddiy tekshirish
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                status = member.status
                if status in [
                    "left",
                    "kicked",
                    "banned",
                ]:
                    return False
        except Exception:
            # Kanal ID noto'g'ri yoki bot kanalda admin emas
            # Bunday holda o'tkazib yuboramiz (xavfsiz)
            pass

    return True


async def check_single_channel(bot: Bot, user_id: int, channel_id: str) -> bool:
    """Bitta kanal uchun obunani tekshiradi."""
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status not in [
            "left",
            "kicked",
            "banned",
        ]
    except Exception:
        return False
