import os
import logging
import asyncio
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
import requests
import secrets
import json

load_dotenv()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Словарь для хранения временных кодов
temp_codes = {}

def get_headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_staff_by_telegram(telegram_id):
    """Найти сотрудника по telegram_id"""
    try:
        headers = get_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?telegram_id=eq.{telegram_id}&select=staff_id,is_verified&is_active=eq.true",
            headers=headers
        )
        if response.status_code == 200 and response.json():
            tg_user = response.json()[0]
            staff_res = requests.get(
                f"{SUPABASE_URL}/rest/v1/staff?id=eq.{tg_user['staff_id']}&select=*,user_roles(roles(name))",
                headers=headers
            )
            if staff_res.status_code == 200 and staff_res.json():
                staff = staff_res.json()[0]
                return staff
        return None
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None

def get_user_role(staff_id):
    """Получить роль сотрудника"""
    try:
        headers = get_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_roles?user_id=eq.{staff_id}&select=roles(name)",
            headers=headers
        )
        if response.status_code == 200 and response.json():
            return response.json()[0]['roles']['name']
        return 'viewer'
    except:
        return 'viewer'

def generate_auth_token(staff_id):
    """Сгенерировать токен для авторизации на сайте"""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(minutes=5)).isoformat()
    
    try:
        headers = get_headers()
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/telegram_users?staff_id=eq.{staff_id}",
            headers=headers,
            json={"auth_token": token, "token_expires": expires_at}
        )
        if response.status_code == 200:
            return token
        return None
    except Exception as e:
        logger.error(f"Ошибка генерации токена: {e}")
        return None

def log_action(staff_id, telegram_id, action, success=True):
    """Запись лога действия"""
    try:
        headers = get_headers()
        data = {
            "staff_id": staff_id,
            "telegram_id": telegram_id,
            "action": action,
            "success": success,
            "created_at": datetime.now().isoformat()
        }
        requests.post(f"{SUPABASE_URL}/rest/v1/auth_logs", headers=headers, json=data)
    except Exception as e:
        logger.error(f"Ошибка записи лога: {e}")

# ==================== КОМАНДЫ БОТА ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с кнопками"""
    user = update.effective_user
    telegram_id = user.id
    username = user.username
    
    staff = get_staff_by_telegram(telegram_id)
    
    if staff:
        role = get_user_role(staff['id'])
        keyboard = [
            [InlineKeyboardButton("🔐 Войти на сайт", callback_data="login")],
            [InlineKeyboardButton("📋 Мои права", callback_data="my_rights")],
            [InlineKeyboardButton("🔄 Новый пароль", callback_data="new_password")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")],
            [InlineKeyboardButton("🆘 Техподдержка", callback_data="support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 Добро пожаловать, {staff['first_name']} {staff['last_name']}!\n\n"
            f"✅ Вы авторизованы в системе.\n"
            f"📋 Ваша роль: {role}\n\n"
            f"🔐 Нажмите «Войти на сайт», чтобы получить ссылку для входа.",
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📝 Привязать аккаунт", callback_data="bind")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")],
            [InlineKeyboardButton("🆘 Связь с поддержкой", callback_data="support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        safe_username = username.replace('@', '') if username else user.first_name
        
        await update.message.reply_text(
            f"👋 *Здравствуйте, {safe_username}!*\n\n"
            f"🤖 Это официальный бот Витебского государственного\n"
            f"   аграрно-технического колледжа.\n\n"
            f"📌 Для доступа к базе данных сотрудников\n"
            f"   необходимо привязать ваш Telegram аккаунт.\n\n"
            f"🔍 *Как узнать свой Telegram ID?*\n"
            f"   1. Напишите боту @userinfobot\n"
            f"   2. Нажмите «Старт»\n"
            f"   3. Скопируйте число (ваш ID)\n\n"
            f"📝 Нажмите «Привязать аккаунт» и сообщите код администратору.\n\n"
            f"*Ваш Telegram ID:* `{telegram_id}`",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help с кнопками"""
    keyboard = [
        [InlineKeyboardButton("📋 Мои права", callback_data="my_rights")],
        [InlineKeyboardButton("🆘 Техподдержка", callback_data="support")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = """
📖 *Помощь по боту*

*Основные команды:*
/start - Главное меню
/status - Проверить права доступа
/help - Эта справка
/sync - Синхронизация с сайтом

*Кнопки:*
🔐 Войти на сайт
📋 Мои права
🔄 Новый пароль
🆘 Техподдержка

*Для администраторов:*
/users - Список сотрудников
/add @username - Добавить сотрудника
/remove @username - Удалить сотрудника
/stats - Статистика
/broadcast - Рассылка

*Как узнать свой Telegram ID?*
👉 @userinfobot

🌐 *Официальный сайт:* vgptksp.vitebsk.by
"""
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - показать права пользователя"""
    user = update.effective_user
    telegram_id = user.id
    
    staff = get_staff_by_telegram(telegram_id)
    
    if staff:
        role = get_user_role(staff['id'])
        await update.message.reply_text(
            f"📋 *Ваша роль:* {role}\n\n"
            f"👤 Сотрудник: {staff['first_name']} {staff['last_name']}\n"
            f"🔐 Статус: Активен\n\n"
            f"Для ввода команд используйте меню.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")],
                [InlineKeyboardButton("🔐 Войти на сайт", callback_data="login")]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ *Ваш аккаунт не привязан к системе!*\n\n"
            "Нажмите «Привязать аккаунт» и сообщите код администратору.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Привязать аккаунт", callback_data="bind")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")]
            ])
        )

async def sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /sync - принудительная синхронизация с сайтом"""
    user = update.effective_user
    telegram_id = user.id
    
    staff = get_staff_by_telegram(telegram_id)
    
    if staff:
        role = get_user_role(staff['id'])
        await update.message.reply_text(
            f"✅ *Синхронизация выполнена!*\n\n"
            f"👤 Сотрудник: {staff['first_name']} {staff['last_name']}\n"
            f"⭐ Роль: {role}\n"
            f"🔐 Статус: Активен\n\n"
            f"📅 Данные актуальны на {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *Вы не авторизованы в системе*\n\n"
            "Возможные причины:\n"
            "• Ваш аккаунт не привязан\n"
            "• Ваш доступ заблокирован администратором\n"
            "• Вы были отвязаны от системы\n\n"
            "Обратитесь к администратору для восстановления доступа.",
            parse_mode='Markdown'
        )

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /support - отправка сообщения администратору"""
    user = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name
    
    # Получаем текст сообщения (всё, что после /support)
    message_text = ' '.join(context.args) if context.args else ''
    
    if not message_text:
        await update.message.reply_text(
            f"🆘 *Техническая поддержка*\n\n"
            f"💬 Опишите вашу проблему одним сообщением.\n"
            f"Администратор свяжется с вами в ближайшее время.\n\n"
            f"📝 *Формат обращения:*\n"
            f"`/support Текст вашего сообщения`\n\n"
            f"✨ *Пример:*\n"
            f"`/support Здравствуйте! Не могу войти на сайт, пишет ошибка авторизации.`\n\n"
            f"✅ После отправки администратор увидит ваше сообщение\n"
            f"и ответит прямо в этот чат.\n\n"
            f"🤖 *Важно:* Если вы не привязаны к системе,\n"
            f"укажите в сообщении ваш Telegram ID: `{telegram_id}`",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, привязан ли пользователь
    staff = get_staff_by_telegram(telegram_id)
    
    if staff:
        user_info = (
            f"👤 *Сотрудник:* {staff['first_name']} {staff['last_name']}\n"
            f"📌 *Должность:* {staff.get('position', '—')}\n"
            f"✅ *Статус:* Привязан к системе\n"
            f"📱 *Telegram ID:* `{telegram_id}`"
        )
    else:
        user_info = (
            f"👤 *Пользователь:* @{username}\n"
            f"📱 *Telegram ID:* `{telegram_id}`\n"
            f"⚠️ *Статус:* Не привязан к системе"
        )
    
    # Отправляем подтверждение пользователю
    await update.message.reply_text(
        f"🆘 *Сообщение отправлено!*\n\n"
        f"✅ Администратор получил ваше обращение.\n"
        f"📝 Ответ придёт в этот чат в ближайшее время.\n\n"
        f"📋 *Ваше сообщение:*\n"
        f"\"{message_text[:300]}{'...' if len(message_text) > 300 else ''}\"",
        parse_mode='Markdown'
    )
    
    # Отправляем сообщение администраторам
    await notify_admins(context, f"📢 *НОВОЕ ОБРАЩЕНИЕ В ТЕХПОДДЕРЖКУ*\n\n{user_info}\n\n📝 *Сообщение:*\n{message_text}")

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Отправить уведомление всем администраторам"""
    try:
        headers = get_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/user_roles?select=user_id,roles(name)&roles.name=in.(super_admin,admin)",
            headers=headers
        )
        
        if response.status_code != 200:
            print("Не удалось получить список администраторов")
            return
        
        admin_ids = []
        for ur in response.json():
            tg_res = requests.get(
                f"{SUPABASE_URL}/rest/v1/telegram_users?staff_id=eq.{ur['user_id']}&select=telegram_id",
                headers=headers
            )
            if tg_res.status_code == 200 and tg_res.json():
                admin_ids.append(tg_res.json()[0]['telegram_id'])
        
        if not admin_ids:
            print("Администраторы не найдены в Telegram")
            return
        
        for admin_id in admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                print(f"Не удалось отправить уведомление админу {admin_id}: {e}")
                
    except Exception as e:
        print(f"Ошибка при отправке уведомления админам: {e}")

# ==================== ОБРАБОТЧИКИ КНОПОК ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    telegram_id = user.id
    data = query.data
    
    if data == "main_menu":
        staff = get_staff_by_telegram(telegram_id)
        if staff:
            role = get_user_role(staff['id'])
            keyboard = [
                [InlineKeyboardButton("🔐 Войти на сайт", callback_data="login")],
                [InlineKeyboardButton("📋 Мои права", callback_data="my_rights")],
                [InlineKeyboardButton("🔄 Новый пароль", callback_data="new_password")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")],
                [InlineKeyboardButton("🆘 Техподдержка", callback_data="support")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"👋 Добро пожаловать, {staff['first_name']} {staff['last_name']}!\n\n"
                f"✅ Вы авторизованы в системе.\n"
                f"📋 Ваша роль: {role}",
                reply_markup=reply_markup
            )
        else:
            keyboard = [
                [InlineKeyboardButton("📝 Привязать аккаунт", callback_data="bind")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")],
                [InlineKeyboardButton("🆘 Связь с поддержкой", callback_data="support")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "👋 Главное меню\n\nДля доступа к системе необходимо привязать аккаунт.",
                reply_markup=reply_markup
            )
    
    elif data == "login":
        staff = get_staff_by_telegram(telegram_id)
        if not staff:
            await query.edit_message_text("❌ Ваш аккаунт не привязан. Нажмите /start и выберите «Привязать аккаунт».")
            return
        
        token = generate_auth_token(staff['id'])
        if token:
            login_url = f"http://127.0.0.1:5000/auth/telegram?token={token}"
            await query.edit_message_text(
                f"🔐 *Ссылка для входа*\n\n"
                f"Нажмите на ссылку ниже, чтобы войти на сайт:\n"
                f"🔗 [Войти на сайт]({login_url})\n\n"
                f"⚠️ Ссылка действительна *5 минут*.\n"
                f"📱 Если ссылка не открывается, скопируйте её в браузер.\n\n"
                f"*Важно:* Если вы не запрашивали вход, проигнорируйте это сообщение.",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            log_action(staff['id'], telegram_id, "login_request", True)
        else:
            await query.edit_message_text("❌ Ошибка генерации ссылки. Попробуйте позже.")
    
    elif data == "my_rights":
        staff = get_staff_by_telegram(telegram_id)
        if staff:
            role = get_user_role(staff['id'])
            await query.edit_message_text(
                f"📋 *Ваша роль:* {role}\n\n"
                f"Для детального списка прав введите /status",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Аккаунт не привязан.")
    
    elif data == "new_password":
        staff = get_staff_by_telegram(telegram_id)
        if staff:
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            
            headers = get_headers()
            requests.post(
                f"{SUPABASE_URL}/rest/v1/user_passwords",
                headers=headers,
                json={"staff_id": staff['id'], "password_hash": new_password, "is_active": True}
            )
            
            await query.edit_message_text(
                f"🔑 *Новый пароль*\n\n"
                f"Ваш новый пароль для входа на сайт:\n"
                f"`{new_password}`\n\n"
                f"⚠️ Сохраните его в надёжном месте.\n"
                f"Пароль можно использовать только один раз.\n\n"
                f"🔐 Логин: {staff.get('phone') or staff.get('id')}",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Аккаунт не привязан.")
    
    elif data == "help":
        await help_command(update, context)
    
    elif data == "support":
        await support_command(update, context)
    
    elif data == "bind":
        code = ''.join(random.choices(string.digits, k=6))
        temp_codes[telegram_id] = {"code": code, "expires": datetime.now() + timedelta(minutes=10)}
        
        await query.edit_message_text(
            f"📝 *Привязка аккаунта*\n\n"
            f"Сообщите администратору этот код:\n"
            f"`{code}`\n\n"
            f"⚠️ Код действителен 10 минут.\n\n"
            f"После подтверждения администратором,\n"
            f"ваш Telegram будет привязан к учётной записи.\n\n"
            f"*Ваш Telegram ID:* `{telegram_id}`\n\n"
            f"🔍 *Не знаете ID?* Напишите @userinfobot",
            parse_mode='Markdown'
        )

# ==================== АДМИНСКИЕ КОМАНДЫ ====================

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /users - список сотрудников, привязанных к боту"""
    user = update.effective_user
    telegram_id = user.id
    
    staff = get_staff_by_telegram(telegram_id)
    if not staff:
        await update.message.reply_text("❌ Вы не авторизованы в системе.")
        return
    
    role = get_user_role(staff['id'])
    if role not in ['super_admin', 'admin']:
        await update.message.reply_text("❌ У вас нет прав для просмотра списка сотрудников.")
        return
    
    try:
        headers = get_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?select=staff_id,telegram_id,telegram_username,is_active,is_verified,staff(last_name,first_name,position)",
            headers=headers
        )
        
        if response.status_code != 200:
            await update.message.reply_text("❌ Ошибка получения списка пользователей")
            return
        
        users = response.json()
        
        if not users:
            await update.message.reply_text("📋 Нет привязанных сотрудников.")
            return
        
        message = "*📋 Список сотрудников в боте:*\n\n"
        for u in users:
            staff_data = u.get('staff', {})
            status_icon = "✅" if u.get('is_active') else "❌"
            verified = "🔐" if u.get('is_verified') else "⏳"
            name = f"{staff_data.get('last_name', '')} {staff_data.get('first_name', '')}".strip()
            role_text = staff_data.get('position', '—')
            tg_username = u.get('telegram_username', '')
            tg_username = tg_username.replace('@', '') if tg_username else ''
            telegram_info = f"@{tg_username}" if tg_username else f"ID: {u.get('telegram_id')}"
            
            message += f"{status_icon} {verified} *{name}*\n"
            message += f"   📌 {role_text}\n"
            message += f"   📱 {telegram_info}\n\n"
        
        if len(message) > 4000:
            await update.message.reply_text("📋 Список слишком длинный. Откройте панель управления ботом на сайте.")
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add @username - добавить сотрудника по Telegram username"""
    user = update.effective_user
    telegram_id = user.id
    
    staff = get_staff_by_telegram(telegram_id)
    if not staff:
        await update.message.reply_text("❌ Вы не авторизованы в системе.")
        return
    
    role = get_user_role(staff['id'])
    if role not in ['super_admin', 'admin']:
        await update.message.reply_text("❌ У вас нет прав для добавления сотрудников.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Укажите Telegram username: `/add @username`", parse_mode='Markdown')
        return
    
    username = context.args[0].replace('@', '')
    
    await update.message.reply_text(
        f"🔗 Для добавления сотрудника @{username}:\n\n"
        f"1. Попросите сотрудника написать боту `/start`\n"
        f"2. Он получит код для привязки\n"
        f"3. Введите код в панели управления ботом на сайте\n\n"
        f"Или привяжите вручную через веб-панель."
    )

async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /remove @username - удалить сотрудника"""
    user = update.effective_user
    telegram_id = user.id
    
    staff = get_staff_by_telegram(telegram_id)
    if not staff:
        await update.message.reply_text("❌ Вы не авторизованы в системе.")
        return
    
    role = get_user_role(staff['id'])
    if role not in ['super_admin', 'admin']:
        await update.message.reply_text("❌ У вас нет прав для удаления сотрудников.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Укажите Telegram username: `/remove @username`", parse_mode='Markdown')
        return
    
    username = context.args[0].replace('@', '')
    
    try:
        headers = get_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?telegram_username=eq.{username}&select=id,staff_id,staff(last_name,first_name)",
            headers=headers
        )
        
        if response.status_code != 200 or not response.json():
            await update.message.reply_text(f"❌ Пользователь @{username} не найден в боте.")
            return
        
        user_data = response.json()[0]
        staff_name = f"{user_data['staff']['first_name']} {user_data['staff']['last_name']}" if user_data.get('staff') else username
        
        delete_res = requests.delete(
            f"{SUPABASE_URL}/rest/v1/telegram_users?id=eq.{user_data['id']}",
            headers=headers
        )
        
        if delete_res.status_code == 200:
            await update.message.reply_text(f"✅ Сотрудник {staff_name} отвязан от Telegram бота.")
            log_action(staff['id'], telegram_id, f"remove_user: {username}", True)
        else:
            await update.message.reply_text("❌ Ошибка при удалении.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика"""
    user = update.effective_user
    telegram_id = user.id
    
    staff = get_staff_by_telegram(telegram_id)
    if not staff:
        await update.message.reply_text("❌ Вы не авторизованы в системе.")
        return
    
    role = get_user_role(staff['id'])
    if role not in ['super_admin', 'admin']:
        await update.message.reply_text("❌ У вас нет прав для просмотра статистики.")
        return
    
    try:
        headers = get_headers()
        
        tg_users = requests.get(f"{SUPABASE_URL}/rest/v1/telegram_users?select=id", headers=headers)
        total_bot_users = len(tg_users.json()) if tg_users.status_code == 200 else 0
        
        tg_active = requests.get(f"{SUPABASE_URL}/rest/v1/telegram_users?is_active=eq.true&select=id", headers=headers)
        active_bot_users = len(tg_active.json()) if tg_active.status_code == 200 else 0
        
        staff_all = requests.get(f"{SUPABASE_URL}/rest/v1/staff?is_active=eq.true&select=id", headers=headers)
        total_staff = len(staff_all.json()) if staff_all.status_code == 200 else 0
        
        groups_res = requests.get(f"{SUPABASE_URL}/rest/v1/groups?is_deleted=eq.false&is_graduated=eq.false&select=id", headers=headers)
        total_groups = len(groups_res.json()) if groups_res.status_code == 200 else 0
        
        students_res = requests.get(f"{SUPABASE_URL}/rest/v1/students?is_deleted=eq.false&select=id", headers=headers)
        total_students = len(students_res.json()) if students_res.status_code == 200 else 0
        
        message = f"""📊 *Статистика системы*

🤖 *Telegram бот:*
• Всего пользователей: {total_bot_users}
• Активных: {active_bot_users}

👥 *Сотрудники:*
• Всего сотрудников: {total_staff}
• Из них в боте: {total_bot_users}

📚 *Учебный процесс:*
• Групп: {total_groups}
• Студентов: {total_students}

📅 Актуально на: {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /broadcast Сообщение - рассылка всем пользователям"""
    user = update.effective_user
    telegram_id = user.id
    
    staff = get_staff_by_telegram(telegram_id)
    if not staff:
        await update.message.reply_text("❌ Вы не авторизованы в системе.")
        return
    
    role = get_user_role(staff['id'])
    if role not in ['super_admin', 'admin']:
        await update.message.reply_text("❌ У вас нет прав для рассылки.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 *Рассылка сообщений*\n\n"
            "Использование: `/broadcast Текст сообщения`\n\n"
            "Пример: `/broadcast Уважаемые сотрудники! Завтра в 10:00 собрание.`",
            parse_mode='Markdown'
        )
        return
    
    broadcast_text = ' '.join(context.args)
    sender_name = f"{staff['first_name']} {staff['last_name']}"
    full_message = f"📢 *Сообщение от администрации*\n\n{broadcast_text}\n\n---\nОтправитель: {sender_name}"
    
    try:
        headers = get_headers()
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/telegram_users?is_active=eq.true&select=telegram_id",
            headers=headers
        )
        
        if response.status_code != 200:
            await update.message.reply_text("❌ Ошибка получения списка пользователей")
            return
        
        users = response.json()
        
        if not users:
            await update.message.reply_text("❌ Нет активных пользователей для рассылки")
            return
        
        await update.message.reply_text(
            f"📢 Начинаю рассылку {len(users)} пользователям...\n\n"
            f"Сообщение: {broadcast_text[:200]}{'...' if len(broadcast_text) > 200 else ''}"
        )
        
        success_count = 0
        fail_count = 0
        
        for u in users:
            try:
                await context.bot.send_message(
                    chat_id=u['telegram_id'],
                    text=full_message,
                    parse_mode='Markdown'
                )
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f"Ошибка отправки {u['telegram_id']}: {e}")
            
            await asyncio.sleep(0.5)
        
        log_action(staff['id'], telegram_id, f"broadcast: {len(users)} users", True)
        
        await update.message.reply_text(
            f"✅ *Рассылка завершена!*\n\n"
            f"📨 Отправлено: {success_count}\n"
            f"❌ Ошибок: {fail_count}\n"
            f"👥 Всего: {len(users)}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при рассылке: {str(e)}")

# ==================== ЗАПУСК БОТА ====================

def main():
    """Запуск бота"""
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды для всех пользователей
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("sync", sync_command))
    application.add_handler(CommandHandler("support", support_command))
    
    # Регистрируем админские команды
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("add", add_user_command))
    application.add_handler(CommandHandler("remove", remove_user_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # Регистрируем обработчики кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("🚀 Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()