import logging
import openai
import mysql.connector
import requests
from langdetect import detect  # For language detection
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from banyabot_credentials import TELEGRAM_BOT_TOKEN, DEEPSEEK_API_KEY, OPENAI_API_KEY, MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

# Store user information in the database
def store_user_info(user):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, language_code) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE username = %s, first_name = %s, last_name = %s, language_code = %s",
            (user.id, user.username, user.first_name, user.last_name, user.language_code,
             user.username, user.first_name, user.last_name, user.language_code)
        )
        connection.commit()
    except Exception as e:
        logger.error(f"Error storing user info: {e}")
    finally:
        cursor.close()
        connection.close()

# Call DeepSeek API for responses
def call_deepseek_api(message, language_code):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": message,
        "language": language_code,
        "tone": "colloquial"
    }
    try:
        response = requests.post("https://api.deepseek.com/v1/chat", headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("response", "Sorry, I couldn't process that.")
    except Exception as e:
        logger.error(f"Error calling DeepSeek API: {e}")
        return "Oops, something went wrong. Try again later, mate."

# Detect language from the user's message
def detect_language(text):
    try:
        return detect(text)
    except:
        return "ru"  # Default to Russian if detection fails

# Call OpenAI API for responses
def call_openai_api(message, language_code):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use "gpt-3.5-turbo" if you prefer or "gpt-4"
            messages=[
                # {"role": "system", "content": f"""
                # You are a bath attendant. Respond in a colloquial tone, with occasional stylish profanity if it fits the context. 
                # Your responses should sound like a laid-back bathhouse worker. As a bathhouse worker, you can discuss any topic grown-up men can discuss.
                # You are witty and clever and sometimes sarcastic. Your guests enjoy your company very much.
                # You can use profanity sparingly when it adds emphasis or humor. Respond in the same language as the user.
                # """},
                {"role": "system", "content": f"""
                Ты настоящий русский банщик. Отвечай в разговорном и расслабленном стиле. Иногда можешь ругнуться и матом, если к месту и с юмором.
                Как настоящий банщик ты можешь обсуждать любые вопросы, которые взрослые мужики могут обсуждать в бане. Ты умный приколист, иногда можешь быть саркастичным.
                В твоей компании всегда всем прикольно и весело. Используй для ответаа не более 180 токенов. Всегда завершай предложения.
                Твои ответы должны быть не более 70 слов и завершаться точкой, восклицательным или вопросительным знаком.
                Отвечай на том же языке, на котором к тебе обращаются.
                """},
                {"role": "user", "content": message}
            ],
            temperature=0.7,  # Adjust for creativity
            max_tokens=250  # Limit response length
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return "Oops, something went wrong. Try again later, mate."


# Handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the message is from a group or private chat
    chat_type = update.message.chat.type
    user = update.message.from_user
    user_message = update.message.text
    print(user_message)

    # Store user info only if it's a private chat
    # if chat_type == "private":
    #     store_user_info(user)

    # Store user info
    store_user_info(user)

    # Detect language from the user's message
    language_code = detect_language(user_message)

    # Call OpenAI API
    language_code = user.language_code or "en"  # Default to English if language_code is not provided
    bot_response = call_openai_api(user_message, language_code)

    # Send response back to the user or group
    await update.message.reply_text(bot_response)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    # Store user info
    store_user_info(user)

    await update.message.reply_text("Welcome, mate! I'm your bath attendant. What can I do for you today?")

# Talk command handler
async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_type = update.message.chat.type

    # Extract the message after the /talk command
    user_message = update.message.text.split(maxsplit=1)  # Split the message into command and text
    if len(user_message) < 2:  # Check if there is no message after /talk
        await update.message.reply_text("Hey, you gotta give me something to work with! Try /talk <your message>.")
        return

    user_message = user_message[1]  # Extract the message part

    # Store user info only if it's a private chat
    # if chat_type == "private":
    #     store_user_info(user)

    # Store user info
    store_user_info(user)

    # Detect language from the user's message
    language_code = detect_language(user_message)

    # Call OpenAI API
    language_code = user.language_code or "en"  # Default to English if language_code is not provided
    bot_response = call_openai_api(user_message, language_code)

    # Send response back to the user or group
    await update.message.reply_text(bot_response)


# Main function to run the bot
def main():
    # Configure OpenAI API
    openai.api_key = OPENAI_API_KEY

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("talk", talk))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()