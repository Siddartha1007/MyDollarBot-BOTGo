import logging
from telebot import types
from datetime import datetime
import helper

option = {}


def run(message, bot):
    helper.read_json()
    chat_id = message.chat.id
    option.pop(chat_id, None)  # Remove temporary choice
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)
    for category_type in helper.geCategoryTypes():
        markup.add(category_type)
    msg = bot.reply_to(message, 'Select Operation', reply_markup=markup)
    bot.register_next_step_handler(msg, post_operation_selection, bot)


def post_operation_selection(message, bot):
    try:
        chat_id = message.chat.id
        op = message.text
        options = helper.geCategoryTypes()
        
        if op not in options.values():
            raise Exception("Sorry, I don't recognize this operation \"{}\"!".format(op))

        category_list = helper.getIncomeCategories() if op == 'income' else helper.getSpendCategories()
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)

        for category in category_list:
            markup.add(category)
        
        msg = bot.reply_to(message, 'Select Category', reply_markup=markup)
        bot.register_next_step_handler(msg, post_category_selection, bot, op)
            
    except Exception as e:
        helper.handle_exception(e, message, bot, logging)


def post_category_selection(message, bot, operation):
    try:
        chat_id = message.chat.id
        selected_category = message.text

        categories_list = helper.getIncomeCategories() if operation == 'income' else helper.getSpendCategories()
        msg = 'earn' if operation == 'income' else 'spend'

        if selected_category not in categories_list:
            raise Exception("Sorry, I don't recognize this category \"{}\"!".format(selected_category))

        option[chat_id] = selected_category
        message = bot.send_message(chat_id, 'How much did you {} on {}? \n(Enter numeric values only)'.format(msg, str(option[chat_id])))
        bot.register_next_step_handler(message, post_amount_input, bot, selected_category, operation)
        
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, 'Oh no! ' + str(e))
        display_text = "\n".join(["/{}: {}".format(c, helper.getCommands()[c]) for c in helper.getCommands()])
        bot.send_message(chat_id, 'Please select a menu option from below:')
        bot.send_message(chat_id, display_text)


def post_amount_input(message, bot, selected_category, operation):
    try:
        chat_id = message.chat.id
        amount_entered = message.text
        amount_value = helper.validate_entered_amount(amount_entered)
        msg = 'earned' if operation == 'income' else 'spent'

        if amount_value == 0:
            raise Exception("Spent amount has to be a non-zero number.")

        date_of_entry = datetime.today().strftime(helper.getDateFormat() + ' ' + helper.getTimeFormat())
        date_str, category_str, amount_str = str(date_of_entry), str(option[chat_id]), str(amount_value)
        user_record = chat_id, "{},{},{}".format(date_str, category_str, amount_str)
        helper.write_json(add_user_record(chat_id, user_record, operation))
        bot.send_message(chat_id, 'The following expenditure has been recorded: You have {} ${} for {} on {}'.format(msg, amount_str, category_str, date_str))
        helper.display_remaining_budget(message, bot, selected_category)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, 'Oh no. ' + str(e))


def add_user_record(chat_id, record_to_be_added, operation):
    data = 'incomeData' if operation == 'income' else 'data'
    user_list = helper.read_json()
    
    if str(chat_id) not in user_list:
        user_list[str(chat_id)] = helper.createNewUserRecord()

    user_list[str(chat_id)][data].append(record_to_be_added[1])
    return user_list
