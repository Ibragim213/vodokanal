import pandas as pd
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# НАСТРОЙКИ - ЗАМЕНИ ТОКЕН НА СВОЙ!
TOKEN = "8449974337:AAEc9GiXQItHTt4jwqp2Auy79XOAAi41EM0"  # ⚠️ ЗАМЕНИ ЭТО!
EXCEL_FILE = "data.xlsx"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Эмодзи для категорий
CATEGORY_EMOJIS = {
    "водоснабжение": "💧",
    "водоотведение": "🚽"
}

# Эмодзи для проблем
PROBLEM_EMOJIS = {
    "порыв": "🚨",
    "утечка": "💦",
    "неудовлетворительное водоснабжение": "⚠️",
    "колонка дворовая": "🏘️",
    "колонка уличная": "🏙️",
    "некачественное водоснабжение": "🔍",
    "закупорка": "🚫",
    "прорыв канализационный": "🔄",
    "обрушение канализационного коллектора": "🏚️"
}


def load_excel_data():
    """Загружаем данные напрямую из Excel"""
    try:
        df = pd.read_excel(EXCEL_FILE)

        # Приводим все к строковому типу и нижнему регистру для поиска
        df['адрес'] = df['адрес'].astype(str).str.lower().str.strip()
        if 'категория' in df.columns:
            df['категория'] = df['категория'].astype(str).str.lower().str.strip()
        if 'специализация' in df.columns:
            df['специализация'] = df['специализация'].astype(str).str.lower().str.strip()
        if 'описание' in df.columns:
            df['описание'] = df['описание'].astype(str)

        print(f"✅ Excel загружен: {len(df)} записей")
        return df

    except Exception as e:
        logging.error(f"❌ Ошибка загрузки Excel: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🔧 *Сервис проверки аварийных ситуаций* 🔧\n\n"
        "Отправь мне адрес, и я проверю информацию о проблемах:\n"
        "• 💧 Водоснабжение\n"
        "• 🚽 Водоотведение\n\n"
        "*Примеры:*\n"
        "магнитогорская 15\n"
        "ленина 20\n"
        "советская 35",
        parse_mode='Markdown'
    )


async def search_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск адреса в Excel"""
    user_address = update.message.text.strip().lower()

    # Загружаем данные из Excel
    df = load_excel_data()
    if df is None:
        await update.message.reply_text("❌ База данных временно недоступна")
        return

    # Ищем адрес (частичное совпадение)
    results = df[df['адрес'].str.contains(user_address, na=False, case=False)]

    if results.empty:
        await update.message.reply_text(
            f"✅ По адресу *{user_address.title()}* аварийных ситуаций не найдено\n\n"
            "Если у вас есть проблема - обратитесь в аварийную службу",
            parse_mode='Markdown'
        )
    else:
        response = f"🔍 *Найдено по адресу:* {user_address.title()}\n\n"

        for _, row in results.iterrows():
            # Получаем данные из строки
            address = row['адрес'].title()
            category = row.get('категория', 'не указана').title()
            problem = row.get('специализация', 'не указана').title()
            description = row.get('описание', '')

            # Выбираем эмодзи
            category_emoji = CATEGORY_EMOJIS.get(row.get('категория', '').lower(), '📋')
            problem_emoji = PROBLEM_EMOJIS.get(row.get('специализация', '').lower(), '🔧')

            response += f"📍 *Адрес:* {address}\n"
            response += f"{category_emoji} *Категория:* {category}\n"
            response += f"{problem_emoji} *Проблема:* {problem}\n"

            if description and str(description).strip() != 'nan':
                response += f"📝 *Описание:* {description}\n"

            response += "─" * 30 + "\n"

        response += f"\n*Всего найдено записей:* {len(results)}"

        await update.message.reply_text(response, parse_mode='Markdown')


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика из Excel"""
    df = load_excel_data()
    if df is None:
        await update.message.reply_text("❌ База данных недоступна")
        return

    total = len(df)

    # Считаем категории
    if 'категория' in df.columns:
        water_supply = len(df[df['категория'].str.lower() == 'водоснабжение'])
        water_drain = len(df[df['категория'].str.lower() == 'водоотведение'])
    else:
        water_supply = water_drain = 0

    response = "📊 *Статистика из Excel*\n\n"
    response += f"💧 Водоснабжение: {water_supply}\n"
    response += f"🚽 Водоотведение: {water_drain}\n"
    response += f"📈 Всего записей: {total}"

    await update.message.reply_text(response, parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logging.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Произошла ошибка, попробуйте позже")


def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_address))
    application.add_error_handler(error_handler)

    # Запускаем бота
    print("🟢 Бот запущен и готов к работе!")
    print("📊 Данные загружаются напрямую из Excel файла")
    application.run_polling()


if __name__ == '__main__':
    main()