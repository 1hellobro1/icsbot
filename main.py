import telebot
import config
from telebot import types
from Modules import findTeachers as findTeacher
from Helpers.DateHelper import is_odd_week
from aenum import Enum
from Helpers import ParserSite
from Modules.infoTeachers import get_teacher_info, prepare_teachers

bot = telebot.TeleBot(config.Token)


class Mode(Enum):
    info = 1,
    find = 2,
    none = 3,
    teach = 4,
    teach2 = 5


mode_switcher = Mode.none.name


def change_mode(mode):
    global mode_switcher
    mode_switcher = mode


def show_no_message(message):
    bot.send_message(message.chat.id, f"На данний час бот не може допомогти з '{message.text}' командою")


@bot.message_handler(commands=['start'])
def send_start(message: types.Message):
    markup_inline = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_depart = types.KeyboardButton(text='Кафедра')
    item_schedule = types.KeyboardButton(text='Розклад')
    item_teacher = types.KeyboardButton(text='Викладачі')

    markup_inline.add(item_depart, item_schedule, item_teacher)
    bot.send_message(message.chat.id, "Ласкаво просимо до боту кафедри *Комп'ютерних та інформаційних систем.*\n"
                                      "Для навігації використовуйте закріплені кнопки нижче.",
                     reply_markup=markup_inline, parse_mode="Markdown")


# \w*\s\w\.\w\.
@bot.message_handler(content_types=['text'], regexp='[А-Яа-я]{4,12}\s\w\.\w*')
def third_line_find_teacher(message: types.Message):
    teacher_name = message.text
    print(mode_switcher)
    if mode_switcher == Mode.find.name:
        text_for_bot = findTeacher.send_teacher(teacher_name)
        if "Перевірте" in text_for_bot:
            bot.send_message(message.chat.id, f"{text_for_bot}\nСпробуйте ще раз")
        else:
            change_mode(Mode.none.name)
            bot.send_message(message.chat.id, f"{text_for_bot}")
    elif mode_switcher == Mode.info.name:
        info = get_teacher_info(teacher_name)
        dlina = len(info)
        print(dlina)
        if dlina > 2:
            bot.send_message(message.chat.id, "Для заданого викладача знайдено таку інформацію:\n"
                                              f"ПІП:  {info['name']}\n"
                                              f"Посада:  {info['position']}\n"
                                              f"Пошта:   {info['mail']}\n")
            change_mode(Mode.none.name)
        else:
            bot.send_message(message.chat.id, "Для заданого викладача не знайдено інформації")
            change_mode(Mode.none.name)
    elif mode_switcher == Mode.teach.name:
        text_print = findTeacher.teacher_schedule(teacher_name, 1)
        bot.send_message(message.chat.id, text_print, parse_mode='HTML')
        change_mode(Mode.none.name)
    elif mode_switcher == Mode.teach2.name:
        text_print = findTeacher.teacher_schedule(teacher_name, 2)
        bot.send_message(message.chat.id, text_print, parse_mode='HTML')
        change_mode(Mode.none.name)
    else:
        show_no_message(message)
        change_mode(Mode.none.name)


@bot.message_handler(content_types=['text'])
def first_line_button(message: types.Message):
    if message.text == 'Кафедра':
        d_markup_reply = types.InlineKeyboardMarkup()
        d_news = types.InlineKeyboardButton(text='Новини', callback_data='l1_news')
        d_info = types.InlineKeyboardButton(text='Контакти', callback_data='l1_info')
        d_markup_reply.add(d_news, d_info)
        bot.send_message(message.chat.id, 'Оберіть будь ласка опцію\n'
                                          '- Отримати інформацію про контакти кафедри\n'
                                          '- Отримати новини за тиждень',
                         reply_markup=d_markup_reply)
    elif message.text == 'Розклад':
        r_markup_reply = types.InlineKeyboardMarkup()
        r_dzvin = types.InlineKeyboardButton(text='Розклад дзвінків', callback_data='sc_dzvin')
        r_teach = types.InlineKeyboardButton(text='Пари у викладача', callback_data='sc_teach')
        r_markup_reply.add(r_dzvin, r_teach)
        bot.send_message(message.chat.id, 'Оберіть будь ласка опцію\n'
                                          '- Отримати розклад дзвінків\n'
                                          '- Отримати розклад пар для викладача',
                         reply_markup=r_markup_reply)
    elif message.text == 'Викладачі':
        t_markup_reply = types.InlineKeyboardMarkup(row_width=3)
        t_info = types.InlineKeyboardButton(text='Інформація', callback_data='l1_info_teach')
        t_feedback = types.InlineKeyboardButton(text='Відгук', callback_data='l1_feed')
        t_find = types.InlineKeyboardButton(text='Знайти', callback_data='l1_find')
        t_markup_reply.add(t_info, t_feedback, t_find)
        bot.send_message(message.chat.id, 'Оберіть будь ласка опцію\n'
                                          '- Отримати інформацію про викладача (посада, почта)\n'
                                          '- Надіслати відгук про якість викладання дисципліни\n'
                                          '- Знайти в якій аудиторії зараз пара у викладача',
                         reply_markup=t_markup_reply)
    else:
        show_no_message(message)


@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('l1'))
def second_line_button(call):
    clicked = call.data.replace('l1_', '')
    if clicked == 'find':
        change_mode("find")
        bot.send_message(call.message.chat.id, "Введіть ПІП викладача українською мовою.\nПриклад: Базилевич В.М.")
    if clicked == 'feed':
        f_markup_reply = types.InlineKeyboardMarkup()
        f_button = types.InlineKeyboardButton(text="Залишити відгук тут",
                                              url=config.FeedbackLink)
        f_markup_reply.add(f_button)
        bot.send_message(call.message.chat.id, "Натисніть нижче, щоб заповнити форму якості викладання дисципліни",
                         reply_markup=f_markup_reply)
    if clicked == 'info_teach':
        it_markup_reply = types.InlineKeyboardMarkup(row_width=2)
        it_all = types.InlineKeyboardButton(text='Всі викладачі', callback_data='l2_all_teachers')
        it_some = types.InlineKeyboardButton(text='Заданий викладач', callback_data='l2_some_teacher')
        it_markup_reply.add(it_all, it_some)
        bot.send_message(call.message.chat.id, 'Оберіть будь ласка опцію\n'
                                               '- Отримати інформацію про всіх викладачів\n'
                                               '- Отримати інформацію для заданого викладача',
                         reply_markup=it_markup_reply)
    if clicked == 'news':
        new_items = ParserSite.get_news()
        if len(new_items) > 0:
            for new_item in new_items:
                title = new_item["title"]
                img = new_item["img"]
                url = new_item["url"]
                print(new_item['title'])
                print(new_item['img'])
                keyboard = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton(text="Детальніше", url=url)
                keyboard.add(button)
                bot.send_message(call.message.chat.id, f"{title}<a href='{img}'>&#8205</a>",
                                 reply_markup=keyboard,
                                 parse_mode="HTML",
                                 disable_web_page_preview=False)
        else:
            bot.send_message(call.message.chat.id, "На данний час актуальних новин немає")
    if clicked == 'info':
        text = "Кафедра:  Інформаційних та комп'ютерних систем\n" \
               "Місцезнаходження:   корпус 4, аудиторія 62\n" \
               "Почта:  ics.department@stu.cn.ua\n" \
               "Телефон:    (0462) 665 194\n" \
               "Завідувач кафедри:  Базилевич Володимир Маркович\n" \
               "Почта:  bazvlamar@stu.cn.ua\n" \
               "Заступник завідувача:   Казнадій Світлана Петрівна\n" \
               "Почта:  s.kaznadiy@stu.cn.ua"
        keyboard = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton(text="Перейти на сайт", url=config.LinkSite)
        keyboard.add(button)
        bot.send_message(call.message.chat.id, text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('l2'))
def third_line_button(call):
    clicked = call.data.replace('l2_', '')
    if clicked == 'all_teachers':
        text = prepare_teachers()
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    if clicked == 'some_teacher':
        change_mode("info")
        bot.send_message(call.message.chat.id, "Введіть ПІП викладача українською мовою.\nПриклад: Базилевич В.М.")


@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('sc'))
def schedule(call):
    clicked = call.data.replace('sc_', '')
    if clicked == 'dzvin':
        week = is_odd_week()
        bot.send_message(call.message.chat.id, f"Зараз {week}.\n\n"
                                          "1 пара   08.00 – 09.20   Перерва - 20 хв\n"
                                          "2 пара   09.40 – 11.00   Перерва - 25 хв\n"
                                          "3 пара   11.25 – 12.45   Перерва - 25 хв\n"
                                          "4 пара   13.10 – 14.30   Перерва - 20 хв\n"
                                          "5 пара   14.50 – 16.10   Перерва - 15 хв\n"
                                          "6 пара   16.25 – 17.45   Перерва - 15 хв\n"
                                          "7 пара   18.00 – 19.20")
    if clicked == 'teach':
        w_markup_reply = types.InlineKeyboardMarkup(row_width=2)
        w1 = types.InlineKeyboardButton(text='1', callback_data='week_1')
        w2 = types.InlineKeyboardButton(text='2', callback_data='week_2')
        w_markup_reply.add(w1, w2)
        bot.send_message(call.message.chat.id, 'Оберіть будь ласка пари за який період бажаете отримати\n'
                                               '- 1 тиждень\n'
                                               '- 2 тижні',
                         reply_markup=w_markup_reply)


@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith('week'))
def week_schedule(call):
    change_mode("teach")
    if call.data == 'week_2':
        change_mode("teach2")
    bot.send_message(call.message.chat.id, "Введіть ПІП викладача українською мовою.\nПриклад: Базилевич В.М.")


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
