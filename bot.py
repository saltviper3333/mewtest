import asyncio
import random
import aiohttp
import time
from .. import loader, utils
from telethon import errors


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
        "qwe_header": "📜 <b>Активные байтинги:</b>\n"
    }

    def __init__(self):
        self.spam_active = False
        # {chat_id: {user_id: start_time}}
        self.q_targets = {}
        self.url = "https://raw.githubusercontent.com/saltviper3333/gdfsfdsfdsf/main/messages.txt"

    async def get_messages(self):
        """Загружаем TXT-шаблон"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    if response.status == 200:
                        data = await response.text()
                        return [line.strip() for line in data.splitlines() if line.strip()]
                    else:
                        return None
        except Exception as e:
            return str(e)

    # === Запуск спама ===
    @loader.command()
    async def sex(self, message):
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
        if self.spam_active:
            self.spam_active = False
            await utils.answer(message, self.strings["spam_stopped"])
        else:
            await utils.answer(message, self.strings["not_running"])

    # === Ставим "байт" ===
    @loader.command()
    async def q(self, message):
        if not message.is_reply:
            return await utils.answer(message, self.strings["q_no_reply"])
        reply_msg = await message.get_reply_message()
        target_id = reply_msg.sender_id
        chat_id = message.chat_id
        self.q_targets.setdefault(chat_id, {})[target_id] = time.time()
        await message.delete()  # мгновенно удаляем команду
        user_name = utils.get_display_name(reply_msg.sender)
        await utils.answer(reply_msg, self.strings["q_added"].format(user_name))

    # === Сбрасываем все цели ===
    @loader.command()
    async def qq(self, message):
        self.q_targets.clear()
        await utils.answer(message, self.strings["qq_done"])

    # === Список активных байтов ===
    @loader.command()
    async def qwe(self, message):
        if not self.q_targets:
            return await utils.answer(message, "❌ <b>Нет активных байтов</b>")
        out = self.strings["qwe_header"]
        now = time.time()
        for chat_id, users in self.q_targets.items():
            try:
                entity = await message.client.get_entity(chat_id)
                if getattr(entity, "title", None):
                    chat_title = f"💬 {entity.title} (группа)"
                else:
                    chat_title = "📩 ЛС"
            except:
                chat_title = str(chat_id)
            out += f"\n<b>{chat_title}</b>:\n"
            for uid, start_time in users.items():
                try:
                    # Получаем участника, чтобы точно достать имя/юзернейм
                    participant = await message.client.get_entity(uid)
                    uname = f"@{participant.username}" if getattr(participant, "username", None) else "—"
                    name_parts = []
                    if getattr(participant, "first_name", None):
                        name_parts.append(participant.first_name)
                    if getattr(participant, "last_name", None):
                        name_parts.append(participant.last_name)
                    name = " ".join(name_parts) if name_parts else str(uid)
                except:
                    uname = "—"
                    name = str(uid)
                elapsed = int(now - start_time)
                h = elapsed // 3600
                m = (elapsed % 3600) // 60
                s = elapsed % 60
                out += f"  ├ 🆔 <code>{uid}</code> | {uname} | {name}\n"
                out += f"  └ ⏳ {h:02}:{m:02}:{s:02}\n"
        await utils.answer(message, out)

    # === Автоответчик по шаблону ===
    async def watcher(self, message):
        if not getattr(message, "sender_id", None):
            return
        chat_id = message.chat_id
        user_id = message.sender_id
        if chat_id in self.q_targets and user_id in self.q_targets[chat_id]:
            phrases = await self.get_messages()
            if not phrases or isinstance(phrases, str):
                return
            try:
                await message.reply(random.choice(phrases))
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                await message.reply(random.choice(phrases))
