import asyncio
import random
import aiohttp
import time
from .. import loader, utils
from telethon import errors, Button, events


@loader.tds
class AutoSpamOnlineMod(loader.Module):
    """Автоспам + автобайт (.q / .qq / .qwe)"""

    strings = {
        "name": "AutoSpamOnline",
        "spam_started": "🚀 <b>ебля запущена!</b>",
        "spam_stopped": "⛔ <b>ебля остановлена</b>",
        "error_download": "❌ <b>Ошибка загрузки фраз:</b> <code>{}</code>",
        "error_no_messages": "❌ <b>В удалённом файле нет сообщений!</b>",
        "already_running": "⚠️ <b>ебля уже запущена</b>",
        "not_running": "❌ <b>ебля не активна</b>",
        "q_no_reply": "⚠️ <b>Используй эту команду ответом на сообщение!</b>",
        "q_added": "✅ <b>Байт включён на {}</b>",
        "qq_done": "🗑 <b>Все байты остановлены</b>",
        "qwe_header": "📜 <b>Активные байтинги:</b>\n",
        "empty_list": "❌ <b>Нет активных байтов</b>"
    }

    def __init__(self):
        self.spam_active = False
        self.q_targets = {}  # {chat_id: {user_id: start_time}}
        self.url = "https://raw.githubusercontent.com/saltviper3333/gdfsfdsfdsf/main/messages.txt"
        self.client = None  # сюда получим клиент после старта

    async def client_ready(self, client, db):
        """Подключение к клиенту и регистрация обработчиков"""
        self.client = client
        # обработчик кнопок
        self.client.add_event_handler(self.inline_button_handler, events.CallbackQuery)
        # обработчик сообщений для автобайта
        self.client.add_event_handler(self.watcher, events.NewMessage)

    async def get_messages(self):
        """Загружаем TXT-шаблон"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    if response.status == 200:
                        return [line.strip() for line in (await response.text()).splitlines() if line.strip()]
        except Exception as e:
            return str(e)
        return None

    @loader.command()
    async def sex(self, message):
        """🚀 Запустить еблю (онлайн-спам)"""
        if self.spam_active:
            return await utils.answer(message, self.strings["already_running"])

        phrases = await self.get_messages()
        if not phrases or isinstance(phrases, str):
            return await utils.answer(message, self.strings["error_no_messages"])

        self.spam_active = True
        await utils.answer(message, self.strings["spam_started"])

        try:
            while self.spam_active:
                await message.client.send_message(message.chat_id, random.choice(phrases))
                await asyncio.sleep(random.uniform(0.08, 0.5))
        except errors.FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        finally:
            self.spam_active = False

    @loader.command()
    async def s(self, message):
        """⛔ Остановить еблю"""
        if self.spam_active:
            self.spam_active = False
            await utils.answer(message, self.strings["spam_stopped"])
        else:
            await utils.answer(message, self.strings["not_running"])

    @loader.command()
    async def q(self, message):
        """🎯 В ответ на сообщение — включить автобайт на пользователя"""
        if not message.is_reply:
            return await utils.answer(message, self.strings["q_no_reply"])

        reply_msg = await message.get_reply_message()
        target_id = reply_msg.sender_id
        chat_id = message.chat_id

        self.q_targets.setdefault(chat_id, {})[target_id] = time.time()

        await message.delete()
        user_name = utils.get_display_name(reply_msg.sender)
        await utils.answer(reply_msg, self.strings["q_added"].format(user_name))

    @loader.command()
    async def qq(self, message):
        """🗑 Остановить все активные байты"""
        self.q_targets.clear()
        await utils.answer(message, self.strings["qq_done"])

    @loader.command()
    async def qwe(self, message):
        """📜 Показать список активных байтингов с кнопками удаления"""
        await self._send_qwe(message)

    async def _send_qwe(self, message_or_event, edited=False):
        """Отрисовка меню"""
        if not self.q_targets:
            if edited:
                await message_or_event.edit(self.strings["empty_list"], buttons=None)
            else:
                await utils.answer(message_or_event, self.strings["empty_list"])
            return

        out = self.strings["qwe_header"]
        buttons = []
        now = time.time()

        for chat_id, users in self.q_targets.items():
            try:
                entity = await self.client.get_entity(chat_id)
                chat_title = f"💬 {entity.title} (группа)" if getattr(entity, "title", None) else "📩 ЛС"
            except:
                chat_title = str(chat_id)
            out += f"\n<b>{chat_title}</b>:\n"

            for uid, start_time in users.items():
                try:
                    user_ent = await self.client.get_entity(uid)
                    uname = f"@{user_ent.username}" if getattr(user_ent, "username", None) else "—"
                    name = " ".join(filter(None, [getattr(user_ent, "first_name", None),
                                                  getattr(user_ent, "last_name", None)])) or str(uid)
                except:
                    uname, name = "—", str(uid)

                elapsed = int(now - start_time)
                h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
                out += f"  ├ 🆔 <code>{uid}</code> | {uname} | {name}\n"
                out += f"  └ ⏳ {h:02}:{m:02}:{s:02}\n"

                buttons.append([Button.inline(f"❌ {name}", data=f"remove_q:{chat_id}:{uid}")])

        if edited:
            await message_or_event.edit(out, buttons=buttons)
        else:
            await self.client.send_message(message_or_event.chat_id, out, buttons=buttons, reply_to=message_or_event.id)

    async def inline_button_handler(self, event: events.CallbackQuery):
        """Нажатие на кнопку удаления"""
        data = event.data.decode("utf-8")
        if not data.startswith("remove_q:"):
            return
        _, chat_id, uid = data.split(":")
        chat_id, uid = int(chat_id), int(uid)

        if chat_id in self.q_targets and uid in self.q_targets[chat_id]:
            del self.q_targets[chat_id][uid]
            if not self.q_targets[chat_id]:
                del self.q_targets[chat_id]

        await event.answer("✅ Байtинг снят", alert=False)
        await self._send_qwe(event, edited=True)

    async def watcher(self, message):
        """Автоответчик"""
        if not getattr(message, "sender_id", None):
            return

        chat_id, user_id = message.chat_id, message.sender_id
        if chat_id in self.q_targets and user_id in self.q_targets[chat_id]:
            phrases = await self.get_messages()
            if phrases and not isinstance(phrases, str):
                try:
                    await message.reply(random.choice(phrases))
                except errors.FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                    await message.reply(random.choice(phrases))
