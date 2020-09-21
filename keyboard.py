import datetime
import telebot


text_about = '''
Что-то очень инетересное по Python
Сcылки на что-то
'''

text_start = '''
Привет, это бот для курса по Python\'у
Ниже можешь узнать о курсе или записаться на него
'''


class Keyboard:
    def __init__(self, bot):
        self.bot = bot

    def display_start(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Зарегистрироваться на курс')
        markup.row('Информация о курсе')
        self.bot.send_message(chat_id=message.from_user.id,
                              text=text_start,
                              reply_markup=markup)

    def display_about(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Зарегистрироваться на курс')
        markup.row('Назад')
        self.bot.send_message(chat_id=message.from_user.id,
                              text=text_about,
                              reply_markup=markup)

    def display_nomer_zachetki(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Назад')
        self.bot.send_message(chat_id=message.from_user.id,
                              text="Введите № зачетки и ФИО",
                              reply_markup=markup)

    def display_proverka(self, message, record_num, FIO):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Да')
        markup.row('Нет')
        # if len(FIO) == 3:
        #     s = '{} {} {} '.format(FIO[0], FIO[1], FIO[2])
        # else:
        #    s = '{} {}  '.format(FIO[0], FIO[1])
        self.bot.send_message(chat_id=message.from_user.id,
                              text="Вы {}\nНомер Вашей зачетки {}?".format(FIO, record_num),
                              reply_markup=markup)

    def display_zapros_dz_reiting(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Запрос своего рейтинга')
        markup.row('Запрос домашнего задания')
        self.bot.send_message(chat_id=message.from_user.id,
                              text="Что вы хотите сделать?",
                              reply_markup=markup)

    def display_stud1(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Запрос своего рейтинга')
        markup.row('Запрос домашнего задания')
        self.bot.send_message(chat_id=message.from_user.id,
                              text="Что вы хотите сделать?",
                              reply_markup=markup)

    def display_zapros_dz(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Последнее домашнее задание')
        markup.row('Домашнее задание по дате')
        markup.row('Все домашние задания')
        markup.row('Назад')
        self.bot.send_message(chat_id=message.from_user.id,
                              text='Какое домашнее задание Вас интересует?',
                              reply_markup=markup)

    def display_zapros_reitinga(self, message):
        self.bot.send_message(chat_id=message.from_user.id,
                              text="Ваш рейтинг: Вы супер умничка :*")


    def display_posled_dz(self, message):
        self.bot.send_message(chat_id=message.from_user.id,
                              text="Последнее домашнее задние: Сделать бота:)")

    def display_dz_po_date(self, message):
        self.bot.send_message(chat_id=message.from_user.id,
                              text="Домашнее задание по дате: Надо доделать типа дату введем и дз выводим")

    def display_vse_dz(self, message):
        self.bot.send_message(chat_id=message.from_user.id,
                              text="Все домашние задания: матстат, питон, бд крч у нас очень много дз")

    def display_admin_start(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Домашнее задание')
        markup.row('Файлы')
        markup.row('Постинг сообщения')
        markup.row('Мониторинг')
        markup.row('Запись прогулов')
        self.bot.send_message(chat_id=message.from_user.id,
                              text='Что вы хотите сделать?',
                              reply_markup=markup)

    def display_admin_dz(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Дать домашнее задание')
        markup.row('Посмотреть домашние задания')
        markup.row('Назад')
        self.bot.send_message(chat_id=message.from_user.id,
                              text='Что вы хотите сделать?',
                              reply_markup=markup)

    def display_zagruzka(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Список студентов')
        markup.row('Текущий рейтинг')
        markup.row('Список на удаление')
        markup.row('Назад')
        self.bot.send_message(chat_id=message.from_user.id,
                              text='Что вас интересует?',
                              reply_markup=markup)

    def display_monitor(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Прогулы')
        markup.row('Успеваемость')
        markup.row('Назад')
        self.bot.send_message(chat_id=message.from_user.id,
                              text='Что вас интересует?',
                              reply_markup=markup)

    def display_work_with_file(self, message):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Загрузить')
        markup.row('Скачать')
        markup.row('Назад')
        self.bot.send_message(chat_id=message.from_user.id,
                              text='Что вас интересует?',
                              reply_markup=markup)