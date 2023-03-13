import tomllib
from pathlib import Path
import logging
from functools import wraps
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram.constants import ChatAction
from typing import TypeVar, Callable, Any, Literal, Optional
import sqlite3

# logger setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger: logging.Logger = logging.getLogger("telegram-quizbot")

# read static config
CONFIG_PATH: Path = Path("./config.toml")
QUIZ_PATH: Path = Path("./quiz.toml")

with open(QUIZ_PATH, "rb") as qp:
    QUIZ_DICT: dict = tomllib.load(qp)

WIN_MESSAGE: str = QUIZ_DICT['winner']
del QUIZ_DICT['winner']
LOSS_MESSAGE: str = QUIZ_DICT['failed']
del QUIZ_DICT['failed']

with open(CONFIG_PATH, "rb") as cp:
    CONFIG_DICT: dict = tomllib.load(cp)

# states for state machine
QUIZ_START, HELP_INFO, QUIZ_QUESTION, QUIZ_WON, QUIZ_LOST = range(5)

# functions
# check if user sending commands or chat is in whitelist
# def restrict_users(func):
#     @wraps(func)
#     def decorator(update, context, *args, **kwargs):
#         userID = update.effective_chat.id
#         if userID not in conf_handler.config['whiteList'].keys():
#             update.message.reply_text(random.choice(conf_handler.config['blackListResponses']))
#             return
#         return func(update, context, *args, **kwargs)
#     return decorator

# typing decorator - for that human feel
def send_typing(func):
    @wraps(func)
    async def command_func(update, context, *args, **kwargs):
        await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return await func(update, context, *args, **kwargs)
    
    return command_func

# decorator to make the bot seem more human
# def send_action(action: ChatAction):
#     def decorator(func):
#         @wraps(func)
#         async def command_func(update, context, *args, **kwargs):
#             await context.bot.send_chat_action(
#                 chat_id=update.effective_message.chat_id, action=action
#             )
#             return await func(update, context, *args, **kwargs)

#         return command_func

#     return decorator


# player handling


# bot async actions
@send_typing
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """Send a message when the command /start is issued."""
    reply_keyboard = [["Yes", "No", "Help!"]]
    if (update.effective_user is not None) and (update.effective_message is not None):
        user: User = update.effective_user
        logger.info(f"User {user.id} has started a quiz")
        await update.effective_message.reply_text(f"Hi {user.full_name}! Welcome to the quizbot.\n\nWould you like to take a quiz?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder="How do you want to proceed?"))

        return QUIZ_START
    else:
        # some other message or user type which are not relevant to this context
        return None

@send_typing 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    if (update.effective_user is not None) and (update.effective_message is not None):
        user: User = update.effective_user
        logger.info(f"User {user.id} canceled the quiz.")
        await update.effective_message.reply_text(
            "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
        )

    return ConversationHandler.END

@send_typing
async def quiz_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """Handles user choice for starting the quiz."""
    reply_keyboard = [["Yes", "No"]]
    if (update.effective_user is not None) and (update.effective_message is not None):
        user: User = update.effective_user
        match update.effective_message.text:
            case "Yes":
                if context.user_data:
                    if context.user_data['won']:
                        # TODO add discount code to message here
                        await update.effective_message.reply_text("You've already beaten the quiz!")
                        return ConversationHandler.END
                    
                    if context.user_data['attempt'] >= CONFIG_DICT['quiz_retries']:
                        await update.effective_message.reply_text("Sorry, you've used up all your attempts!")
                        return ConversationHandler.END
                    
                    context.user_data['attempts'] += 1
                else:
                    # TODO: check user state from DB
                    context.user_data.update({'id':user.id,
                                              'won': False,
                                              'attempt': 1,
                                              'questions': None,
                                              'question_num':None,
                                              'discount_code':None})

                await update.effective_message.reply_text("Beaming up your questions...")
                context.user_data['questions'] = random.sample(list(QUIZ_DICT.keys()), CONFIG_DICT['quiz_questions'])
                context.user_data['question_num'] = 0
                
                return QUIZ_QUESTION
            case "No":
                await update.effective_message.reply_text("If you are sure that's what you want to do...")
                return ConversationHandler.END
            case "Help!":
                await update.effective_message.reply_text(f"This is an automated quiz which may have a tasty treat at the end, but only if you score high enough!\n\nBe quick, you only have {CONFIG_DICT['max_question_time_seconds']} seconds to answer each question!\n\nWould you like to take the quiz now?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder="How do you want to proceed?"))
                return QUIZ_START
            case _:
                return None


def main() -> None:
    # make chat app and pass bot token
    application: Application = (
        Application.builder().token(CONFIG_DICT["telegram_api_token"]).build()
    )

    quiz: ConversationHandler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QUIZ_START: [MessageHandler(filters.Regex("^(Yes|No|Help!)$"), quiz_choice)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(quiz)

    application.run_polling()


if __name__ == "__main__":
    main()
