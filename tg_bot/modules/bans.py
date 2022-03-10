import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("आप किसी यूजर को टैग नहीं कर रहे हैं")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("मुझे यूजर नहीं मिल रहा है")
        return ""
    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("कास मैं एडमिन्स को हटा सकता ")
        return ""

    if user_id == bot.id:
        message.reply_text("मैं खुद को हटाने वाला नहीं हूं, आप पागल हैं")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), 
                                                  mention_html(member.user.id, member.user.first_name), user_id)

    reply = "{} को निकाल दिया!" .format(mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>• Reason:</b> {}".format(reason)
        reply += "\n<b>कारण:</b> <i>{}</i>".format(reason)

    try:
        chat.kick_member(user_id)
        keyboard = []
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply Message Not Found":
            # Do not reply
            message.reply_text('रिप्लाई मैसेज नहीं मिला...!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("मैं उसे हटा नहीं सकता")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("आप किसी यूजर को टैग नहीं कर रहे हैं")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("मुझे यूजर नहीं मिल रहा है")
        return ""
    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("कास मैं एडमिन्स को हटा सकता")
        return ""

    if user_id == bot.id:
        message.reply_text("मैं खुद को हटाने वाला नहीं हूं, आप पागल हैं")
        return ""

    if not reason:
        message.reply_text("आपने इस यूजर को निकालने के लिए एक समय नहीं दिया है")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMPBAN" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>" \
          "\n<b>• Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                                                mention_html(member.user.id, member.user.first_name), 
                                                                             user_id, time_val)
    if reason:
        log += "\n<b>• कारण:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        keyboard = []
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)  # banhammer marie sticker
        reply = "{} को निकाल दिया क्योंकि {}!".format(mention_html(member.user.id, member.user.first_name),time_val)
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply Message Not Found":
            # Do not reply
            message.reply_text("यूजर हटा दिया क्योंकि {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("मैं उसे हटा नहीं सकता")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("मुझे यूजर नहीं मिल रहा है")
        return ""
    if is_user_ban_protected(chat, user_id):
        message.reply_text("कास मैं एडमिन्स को हटा सकता...")
        return ""

    if user_id == bot.id:
        message.reply_text("हाँ, मैं ऐसा नहीं करने जा रहा हूँ,मुझे ही निकाल रहे हो")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} को लात मारकर निकाल दिया!".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)

        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>• Admin:</b> {}" \
              "\n<b>• User:</b> {}" \
              "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title),
                                                      mention_html(user.id, user.first_name),
                                                      mention_html(member.user.id, member.user.first_name), user_id)
        if reason:
            log += "\n<b>• कारण:</b> {}".format(reason)

        return log

    else:
        message.reply_text("मैं उसे हटा नहीं सकता")

    return ""


@run_async
@bot_admin
@can_restrict
@loggable
def banme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("काश मैं कर सकता ... लेकिन आप एक एडमिन हैं")
        return

    res = update.effective_chat.kick_member(user_id)
    if res:
        update.effective_message.reply_text("कोई बात नहीं,निकल दिया")
        return (
            "<b>{}:</b>"
            "\n#BANME"
            "\n<b>User:</b> {}"
            "\n<b>ID:</b> <code>{}</code>".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                user_id,
            )
        )


    else:
        update.effective_message.reply_text("है? मैं नहीं कर सकता :/")
        
@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("काश मैं कर सकता ... लेकिन आप एक एडमिन हैं")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("कोई बात नहीं")
    else:
        update.effective_message.reply_text("है? मैं नहीं कर सकता :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("मुझे यूजर नहीं मिल रहा है")
        return ""
    if user_id == bot.id:
        message.reply_text("अगर मैं यहाँ नहीं होता तो मैं खुद को कैसे हटाता ...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("आप किसी ऐसे व्यक्ति को अनबन करने की कोशिश कर रहे हैं जो पहले से ही चैट में है?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("हां, यह यूजर फिर से शामिल हो सकता है!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title),
                                                  mention_html(user.id, user.first_name),
                                                  mention_html(member.user.id, member.user.first_name), user_id)
    if reason:
        log += "\n<b>• कारण:</b> {}".format(reason)

    return log

@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def sban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    update.effective_message.delete()

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        return ""

    if user_id == bot.id:
        return ""

    log = "<b>{}:</b>" \
          "\n#SILENT BAN" \
          "\n<b>• Admin:</b> {}" \
          "\n<b>• User:</b> {}" \
          "\n<b>• ID:</b> <code>{}</code>".format(html.escape(chat.title), mention_html(user.id, user.first_name), 
                                                  mention_html(member.user.id, member.user.first_name), user_id)
    if reason:
        log += "\n<b>• कारण:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            return log
        LOGGER.warning(update)
        LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id, excp.message)
    return ""

__help__ = """
 - /kickme: आदेश जारी करने वाले यूजर को हट ता है.
 - /banme: आदेश जारी करने वाले यूजर को निकालता है..

*Admin only:*
 - /ban <userhandle>: यूजर को ग्रुप से निकालता है
 - /sban <userhandle>: चुप चाप ग्रुप से निकालता है
 - /tban <userhandle> x(m/h/d):  यूजर को ग्रुप से निकालता है समय x के लिए  m = मिनट, h = घंटों, d = दिन.
 - /unban <userhandle>: unbans a user. (via handle, or reply)
 - /kick <userhandle>: यूजर को हट ता है.)
"""

__mod_name__ = "Bans"

BAN_HANDLER = DisableAbleCommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
BANME_HANDLER = DisableAbleCommandHandler("banme", banme, filters=Filters.group)
SBAN_HANDLER = CommandHandler("sban", sban, pass_args=True, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)
dispatcher.add_handler(SBAN_HANDLER)
