import telebot
import psycopg2 as ps
import db
from re import split as spl
from keyboard import Keyboard
import telegramcalendar as tgc
from io import BytesIO
import wok_with_excel
from apscheduler.schedulers.background import BackgroundScheduler
import os
from flask import Flask, request
import time

# ваш токен
TOKEN = '' 
# пароль, чтобы залогиниться как админ
MAIN_PASSWORD = ""
bot = telebot.TeleBot(TOKEN)
keyboard = Keyboard(bot)
DATABASE_URL = os.environ['DATABASE_URL']

pos_for_none = {}
dict_for_none = {}  # key = user_id, value - class student
task_description = ''
deadline_date = tgc.datetime.datetime.now()
max_mark = ''
post_text = ''
# main_id = 

class student:
    def __init__(self, name, surname, midname, record_num):
        self.name = name
        self.surname = surname
        self.midname = midname
        self.record_num = record_num


def close_conn(database):
    try:
        database.cursor.close()
    except Exception:
        pass
    try:
        database.connection.close()
    except Exception:
        pass



def open_conn(database):
    try:
        database.connection = ps.connect(DATABASE_URL, sslmode='require')
        database.cursor = database.connection.cursor()
        scheduler.add_job(close_conn, 'date',
                          next_run_time=tgc.datetime.datetime.now() + tgc.datetime.timedelta(minutes = 10),
                          args=[database])
    except Exception:
        bot.send_message(main_id, 'connection не открылся')



def exception_handler(func):
    def wrapper(smth):
        try:
            func(smth)
        except ps.errors.UndefinedTable as ex:
            print(ex)
            database.connection.rollback()
            try:
                database.create_access()
            except ps.errors.DuplicateTable:
                database.connection.rollback()
            try:
                database.create_students()
            except ps.errors.DuplicateTable:
                database.connection.rollback()
            try:
                database.create_tasks()
            except ps.errors.DuplicateTable:
                database.connection.rollback()
            try:
                database.create_trigger_delete_student()
            except ps.errors.DuplicateObject:
                database.connection.rollback()
            if isinstance(smth, telebot.types.Message):
                bot.send_message(chat_id=smth.from_user.id, text='Ошибка подключения к базе, пропробуйте позже')
            elif isinstance(smth, telebot.types.CallbackQuery):
                bot.send_message(chat_id=smth.message.from_user.id, text='Ошибка подключения к базе, пропробуйте позже')
        except Exception as ex:
            bot.send_message(main_id, str(ex))
            database.connection.rollback()
    return wrapper


@bot.message_handler(commands=['start'])
@exception_handler
def start_hand(message):
    """
    В зависимости от прав доступа выводить их первый блок интерфейса
    """
    # для none
    user = database.find_user(message.from_user.id)
    if user is None:
        keyboard.display_start(message)
    else:
        if not user[1]:
            keyboard.display_zapros_dz_reiting(message)
            database.update_position(message.from_user.id, 
                                    )
        else:
            keyboard.display_admin_start(message)
            database.update_position(message.from_user.id, 1)


@bot.message_handler(commands=['login'])
@exception_handler
def login_hand(message):
    splited_text = spl('[ ]+', message.text)
    done = False
    if len(splited_text) == 2:
        password = splited_text[1]
        if password == MAIN_PASSWORD:
            done = True
    if done:
        # Т.к. нет еще начальных интерфейсов для админа / студента
        # нужно не забыть, что еще добавляем в таблицу позиции!
        try:
            database.add_user(user_id=message.from_user.id, access_code=True)
            # здесь еще добавление 0 позиции интерфеса админа
            database.add_position(user_id=message.from_user.id, pos=1)
        except ps.errors.UndefinedTable:
            # ВАЖНО!!!!!!!!!!
            # после неудавшейся операции нужно откатывать транзакцию
            # Иначе будет ошибка вида, что транзакция прервана, все игнорируется
            database.connection.rollback()
            database.create_access()
            database.create_students()
            database.create_tasks()
            # database.create_position()
            database.add_user(user_id=message.from_user.id, access_code=True)
            # здесь еще добавление 0 позиции интерфеса админа
            database.add_position(user_id=message.from_user.id, pos=1)
            # здесь должен быть правильный вызов ответа из keyboard
            # с новым интерфейсом
            #
            bot.send_message(chat_id=message.from_user.id,
                             text='Вы авторизированы с правами доступа администратора')
            keyboard.display_admin_start(message)
        except ps.errors.UniqueViolation as ex:
            database.connection.rollback()
            # тип есть в базе
            # print('Есть в базе')
            bot.send_message(chat_id=message.from_user.id,
                             text='Вы уже авторизированы!')
            keyboard.display_admin_start(message)
        else:
            # здесь должен быть правильный вызов ответа из keyboard
            # с новым интерфейсом
            bot.send_message(chat_id=message.from_user.id,
                             text='Вы авторизированы с правами доступа администратора')
            keyboard.display_admin_start(message)
    else:
        bot.reply_to(message, 'Отказано в доступе!')


@bot.message_handler(func=lambda msg: msg.text == 'Информация о курсе', content_types=['text'])
def about_hand(message):
    keyboard.display_about(message)


@bot.message_handler(func=lambda msg: msg.text == 'Назад', content_types=['text'])
@exception_handler
def back_hand(message):
    """
    Тут следуют проверки, есть ли в базе "Доступ"
    Если есть, то вернуться назад по интерфейсу(или  его начало)
    Если нет - неизвестный пользователь и вывести старт
    """
    if database.find_user(message.from_user.id) is None:
        keyboard.display_start(message)
    else:
        pos = database.find_position(message.from_user.id)
        pos = pos // 10
        if pos == 2:
            database.update_position(message.from_user.id, 2)
            keyboard.display_zapros_dz_reiting(message)
        elif pos == 1:
            database.update_position(message.from_user.id, 0)
            keyboard.display_admin_start(message)
        elif pos == 10:
            database.update_position(message.from_user.id, 10)
            keyboard.display_admin_dz(message)
        elif pos in [11, 111]:
            database.update_position(message.from_user.id, 11)
            keyboard.display_work_with_file(message)


@bot.message_handler(func=lambda msg: msg.text == 'Да', content_types=['text'])
@exception_handler
def zareg(message):
    global task_description
    global max_mark
    pos = database.find_position(message.from_user.id)
    if pos is None:
        if message.from_user.id in pos_for_none.keys():
            if pos_for_none[message.from_user.id] == 32:
                pers = dict_for_none[message.from_user.id]
                user_id = message.from_user.id
                try:
                    database.add_student_with_id(pers.name, pers.surname,
                                                 pers.midname, pers.record_num,
                                                 user_id)
                except ps.errors.UndefinedTable:
                    database.connection.rollback()
                    database.create_access()
                    database.create_students()
                    database.create_tasks()
                    database.add_user(user_id, False)
                    database.add_position(user_id, 2)
                    database.add_student_with_id(pers.name, pers.surname,
                                                 pers.midname, pers.record_num,
                                                 user_id)
                    bot.send_message(chat_id=message.from_user.id,
                                     text='Вы записались на курс')
                    keyboard.display_zapros_dz_reiting(message)
                except ps.errors.UniqueViolation:
                    database.connection.rollback()
                    database_stud = database.find_student_with_record(pers.record_num)
                    if database_stud is not None: #Существует такой же userid
                        if database_stud[0] == pers.name and \
                                database_stud[1] == pers.surname and \
                                database_stud[2] == pers.midname and \
                                database_stud[3] == pers.record_num:
                            database.update_student_with_record(pers.record_num, user_id,
                                                                *(pers.name, pers.surname, pers.midname))
                            database.add_user(user_id, False)
                            database.add_position(user_id, 2)
                            bot.send_message(chat_id=message.from_user.id,
                                             text='Вы записались на курс')
                            keyboard.display_zapros_dz_reiting(message)
                        else:
                            bot.send_message(user_id, 'Студент с таким номером зачетки зарегистрирован\n')
                            keyboard.display_start(message)
                    else:
                        bot.send_message(user_id, 'Вы вышли из курса!\nЕсли хотите вернуться, обратитесь к преподавателю')
                else:
                    database.add_user(user_id, False)
                    database.add_position(user_id, 2)
                    bot.send_message(message.from_user.id, 'Вы записались на курс')
                    keyboard.display_zapros_dz_reiting(message)
        else:
            pos_for_none.update({message.from_user.id: 3})
            keyboard.display_start(message)
    elif pos == 102:
        if task_description != '':
            keyboard.display_admin_dz(message)
            database.update_position(message.from_user.id, 10)
            database.add_tasks(tgc.datetime.datetime.now(), deadline_date,
                               task_description, int(max_mark))
            task_description = ''
            max_mark = ''
    elif pos == 101:
        bot.send_message(chat_id=message.from_user.id,
                         text='Введите домашнее задание\nПоследним должен быть макс. балл')
        task_description = ''
        max_mark = ''
        database.update_position(message.from_user.id, 102)
    elif pos == 12:
        if post_text is None:
            post_message(message)
        else:
            recipients = database.find_student_not_none_userid()
            for person in recipients:
                bot.send_message(chat_id=person[0], text=post_text + '\n(c)Преподаватель')
            keyboard.display_admin_start(message)
            database.update_position(message.from_user.id, 1)


@bot.message_handler(func=lambda msg: msg.text == 'Нет', content_types=['text'])
@exception_handler
def zareg(message):
    pos = database.find_position(message.from_user.id)
    if pos is None:
        registration_on_course(message)
    elif pos == 101:
        now = tgc.datetime.datetime.now()  # Текущая дата
        markup = tgc.create_calendar(now.year, now.month)
        bot.send_message(message.from_user.id, "Пожалуйста, выберите дату сдачи домашнего заадания",
                         reply_markup=markup)
        database.update_position(message.from_user.id, 101)
    elif pos == 102:
        # markup = telebot.types.ReplyKeyboardMarkup(True, False)
        bot.send_message(chat_id=message.from_user.id,
                         text='Введите домашнее задание')
        database.update_position(message.from_user.id, 102)
    elif pos == 12:
        post_message(message)


@bot.message_handler(func=lambda msg: msg.text == 'Запрос домашнего задания' or
                                      msg.text == 'Посмотреть домашние задания', content_types=['text'])
@exception_handler
def dom_zad(message):
    pos = database.find_position(message.from_user.id)
    if pos == 2:
        database.update_position(message.from_user.id, 21)
        keyboard.display_zapros_dz(message)
    elif pos == 10:
        database.update_position(message.from_user.id, 101)
        keyboard.display_zapros_dz(message)


@bot.message_handler(func=lambda msg: msg.text == 'Последнее домашнее задание', content_types=['text'])
@exception_handler
def dom_zad(message):
    pos = database.find_position(message.from_user.id)
    dz = database.find_last_task()
    text = ''
    if dz is None:
        text += 'У вас нет ДЗ'
    else:
        date = tgc.datetime.date(dz[2].year, dz[2].month, dz[2].day)
        text += 'Номер дз {}\nОписание: {}\nДедлайн: {}'.format(dz[0], dz[1], date)
    if pos == 21:
        database.update_position(message.from_user.id, 2)
        bot.send_message(message.from_user.id, text)
        keyboard.display_zapros_dz_reiting(message)
    elif pos == 101:
        database.update_position(message.from_user.id, 10)
        bot.send_message(message.from_user.id, text)
        keyboard.display_admin_dz(message)


@bot.message_handler(func=lambda msg: msg.text == 'Домашнее задание по дате', content_types=['text'])
@exception_handler
def dom_zad(message):
    pos = database.find_position(message.from_user.id)
    if pos == 21:
        database.update_position(message.from_user.id, 212)
        now = tgc.datetime.datetime.now()  # Текущая дата
        markup = tgc.create_calendar(now.year, now.month)
        bot.send_message(message.from_user.id, "Пожалуйста, выберите дату домашнего задания", reply_markup=markup)
        #for task in database.find_tasks_by_date(date_given=)
        #keyboard.display_zapros_dz_reiting(message)
    elif pos == 101:
        database.update_position(message.from_user.id, 1012)
        now = tgc.datetime.datetime.now()  # Текущая дата
        markup = tgc.create_calendar(now.year, now.month)
        bot.send_message(message.from_user.id, "Пожалуйста, выберите дату домашнего задания", reply_markup=markup)
        #keyboard.display_dz_po_date(message)
        #keyboard.display_admin_dz(message)


@bot.message_handler(func=lambda msg: msg.text == 'Все домашние задания', content_types=['text'])
@exception_handler
def dom_zad(message):
    pos = database.find_position(message.from_user.id)
    if pos == 21 or pos == 101:
        dz = database.find_tasks()
        if not dz:
            bot.send_message(message.from_user.id,'У Вас еще нет ДЗ')
        else:
            for i in dz:
                text = 'Номер дз: {}'.format(i[0])
                text += '\nВыдано: {}'.format(i[1])
                text += '\nОписание: {}'.format(i[2])
                bot.send_message(message.from_user.id, text)
        start_hand(message)

@bot.message_handler(func=lambda msg: msg.text == 'Запрос своего рейтинга', content_types=['text'])
@exception_handler
def zapros(message):
    #database.update_position(message.from_user.id, 2)
    # keyboard.display_zapros_reitinga(message)
    stud = database.find_student_with_userid(message.from_user.id)
    reiting = database.accounting_mark(stud[3])
    bot.send_message(message.from_user.id, 'Ваш рейтинг: {} из {}'.format(reiting[0], reiting[1]))
    keyboard.display_zapros_dz_reiting(message)
    database.update_position(message.from_user.id, 2)


@bot.message_handler(func=lambda msg: msg.text == 'Зарегистрироваться на курс' or msg.text == 'Нет',
                     content_types=['text'])
@exception_handler
def registration_on_course(message):
    pos_for_none.update({message.from_user.id: 31})
    keyboard.display_nomer_zachetki(message)


@bot.message_handler(func=lambda msg: msg.text == 'Домашнее задание', content_types=['text'])
@exception_handler
def ad_dz(message):
    keyboard.display_admin_dz(message)
    database.update_position(message.from_user.id, 10)


@bot.message_handler(func=lambda msg: msg.text == 'Файлы', content_types=['text'])
@exception_handler
def add_files(message):
    keyboard.display_work_with_file(message)
    database.update_position(message.from_user.id, 11)


@bot.message_handler(func=lambda msg: msg.text == 'Загрузить', content_types=['text'])
@exception_handler
def add_files_to_database(message):
    keyboard.display_zagruzka(message)
    database.update_position(message.from_user.id, 111)


@bot.message_handler(func=lambda msg: msg.text == 'Скачать', content_types=['text'])
@exception_handler
def add_files_to_database(message):
    keyboard.display_zagruzka(message)
    database.update_position(message.from_user.id, 112)


@bot.message_handler(func=lambda msg: msg.text == 'Постинг сообщения', content_types=['text'])
@exception_handler
def post_message(message):
    bot.send_message(chat_id=message.from_user.id,
                     text='Введите сообщение, которое хотите запостить',
                     reply_markup=telebot.types.ReplyKeyboardRemove())
    database.update_position(message.from_user.id, 12)
    global post_text
    post_text = ''


@bot.message_handler(func=lambda msg: msg.text == 'Мониторинг', content_types=['text'])
@exception_handler
def ad_dz(message):
    keyboard.display_monitor(message)
    database.update_position(message.from_user.id, 13)


@bot.message_handler(func=lambda msg: msg.text == 'Запись прогулов', content_types=['text'])
@exception_handler
def ad_dz(message):
    database.update_position(message.from_user.id, 14)
    bot.send_message(chat_id=message.from_user.id,
                     text='Введите ФИО прогулявших')


@bot.message_handler(func=lambda msg: msg.text == 'Прогулы', content_types=['text'])
@exception_handler
def ad_dz(message):
    bot.send_message(chat_id=message.from_user.id,
                     text='Прогуляшие')


@bot.message_handler(func=lambda msg: msg.text == 'Успеваемость', content_types=['text'])
@exception_handler
def display_deptors(message):
    deptors = database.list_of_deptors(tgc.datetime.datetime.now())
    print(deptors)
    if not deptors:
        bot.send_message(message.from_user.id, 'Должников нет')
    else:
        text = 'Должники:\n'
        for i in deptors.keys():
            text += '{} {}\n'.format(deptors[i][0], deptors[i][1])
        bot.send_message(message.from_user.id, text)
    start_hand(message)


@bot.message_handler(func=lambda msg: msg.text == 'Список студентов', content_types=['text'])
@exception_handler
def ad_dz(message):
    pos = database.find_position(message.from_user.id)
    if pos == 111:
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Назад')
        database.update_position(message.from_user.id, 1111)
        bot.send_message(chat_id=message.from_user.id,
                         text='Пришлите файл со студентами',
                         reply_markup=markup)
    else:
        add_files(message)
        wok_with_excel.from_database_to_excel_of_students_list(database)
        bot.send_document(chat_id=message.from_user.id, data=open('students.xlsx', 'rb'))


@bot.message_handler(func=lambda msg: msg.text == 'Текущий рейтинг', content_types=['text'])
@exception_handler
def ad_dz(message):
    pos = database.find_position(message.from_user.id)
    if pos == 111:
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Назад')
        database.update_position(message.from_user.id, 1112)
        bot.send_message(chat_id=message.from_user.id,
                         text='Пришлите файл с текущим рейтингом',
                         reply_markup=markup)
    else:
        add_files(message)
        wok_with_excel.save_marks_to_book(database)
        bot.send_document(chat_id=message.from_user.id, data=open('marks.xlsx', 'rb'))


@bot.message_handler(func=lambda msg: msg.text == 'Список на удаление', content_types=['text'])
@exception_handler
def add_delete_list(message):
    pos = database.find_position(message.from_user.id)
    if pos == 111:
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.row('Назад')
        database.update_position(message.from_user.id, 1113)
        bot.send_message(chat_id=message.from_user.id,
                         text='Пришлите файл со списком на удаление\n'
                              'Формат аналогичен файлу для добавления студентов',
                         reply_markup=markup)
    else:
        add_files(message)
        wok_with_excel.from_database_to_excel_of_students_list(database)
        bot.send_document(chat_id=message.from_user.id, data=open('students.xlsx', 'rb'))


@bot.message_handler(func=lambda mess: mess.text == 'Дать домашнее задание', content_types=['text'])
@exception_handler
def get_calendar(message):
    now = tgc.datetime.datetime.now()  # Текущая дата
    markup = tgc.create_calendar(now.year, now.month)
    bot.send_message(message.from_user.id, "Пожалуйста, выберите дату сдачи домашнего задания", reply_markup=markup)
    database.update_position(message.from_user.id, 101)


@bot.callback_query_handler(func=lambda call: tgc.separate_callback_data(call.data)[0] in
                                              ['IGNORE', 'PREV-MONTH', 'NEXT-MONTH', 'DAY'])
@exception_handler
def keyboard_input_text(call):
    pos = database.find_position(call.message.chat.id)
    if pos == 101 or pos == 212 or pos == 1012:
        (action, year, month, day) = tgc.separate_callback_data(call.data)
        curr = tgc.datetime.date(int(year), int(month), 1)
        if action == "IGNORE":
            # Продолжаем игнорить неюзабильные кнопки
            bot.answer_callback_query(callback_query_id=call.id)
        elif action == "DAY":
            # Выбран день
            # Cкрываем календарь (изменяем сообщение, не посылая markup)
            bot.edit_message_text(text=call.message.text,
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id)
            if pos == 101:
                ret_data = tgc.datetime.date(int(year), int(month), int(day))
                gg = ret_data.year
                mm = ret_data.month
                dd = ret_data.day
                global deadline_date
                deadline_date = ret_data
                markup = telebot.types.ReplyKeyboardMarkup(True, False)
                markup.row('Да')
                markup.row('Нет')
                bot.send_message(call.message.chat.id, "Домашнее задание на {}.{}.{}".format(dd, mm, gg),
                                 reply_markup=markup)
                database.update_position(call.message.chat.id, 101)
            else:
                dz = database.find_tasks_by_date(tgc.datetime.date(int(year), int(month), int(day)))
                if not dz:
                    bot.send_message(call.from_user.id, 'У Вас нет ДЗ на эту дату')
                else:
                    for i in dz:
                        text = 'Номер дз: {}'.format(i[0])
                        text += '\nОписание: {}'.format(i[1])
                        text += '\nДедлайн: {}'.format(i[2])
                        text += '\nМакс. балл: {}'.format(i[3])
                        bot.send_message(call.message.chat.id, text)
                start_hand(call)
        elif action == "PREV-MONTH":
            pre = curr - tgc.datetime.timedelta(days=1)
            bot.edit_message_text(text=call.message.text,
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=tgc.create_calendar(int(pre.year), int(pre.month)))
        elif action == "NEXT-MONTH":
            ne = curr + tgc.datetime.timedelta(days=31)
            bot.edit_message_text(text=call.message.text,
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=tgc.create_calendar(int(ne.year), int(ne.month)))
        else:
            bot.answer_callback_query(callback_query_id=call.id, text="Something went wrong!")
    else:  # Скрываем календарь.
        bot.edit_message_text(text=call.message.text,
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)


@bot.message_handler(content_types=['document'])
@exception_handler
def get_students(message):
    pos = database.find_position(message.from_user.id)
    if pos is None:
        keyboard.display_start(message)
    elif database.find_user(message.from_user.id):
        if message.document.file_name[-4::1] == 'xlsx':
            try:
                if pos == 1111:
                    file_info = bot.get_file(message.document.file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    wok_with_excel.from_excel_to_database_of_students_list(database, BytesIO(downloaded_file))
                elif pos == 1112:
                    file_info = bot.get_file(message.document.file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    wok_with_excel.download_marks_from_book(database, BytesIO(downloaded_file))
                elif pos == 1113:
                    file_info = bot.get_file(message.document.file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    deleted = wok_with_excel.delete_students_from_database(database,BytesIO(downloaded_file))
                    markup = telebot.types.ReplyKeyboardMarkup(True, False)
                    markup.row('Зарегистрироваться на курс')
                    markup.row('Информация о курсе')
                    for user_id in deleted:
                        bot.send_message(chat_id=user_id, text='Вас удалили из курса!', reply_markup= markup)
            except wok_with_excel.DowloandError as ex:
                bot.send_message(message.from_user.id, ex.message)
            else:
                add_files(message)
        else:
            bot.send_message(message.from_user.id, 'Файл не соответсвует формату!')


@bot.message_handler(func=lambda mess: mess.text != '', content_types=['text'])
@exception_handler
def zareg(message):
    s1 = message.text
    splitted = s1.split()
    pos = database.find_position(message.from_user.id)
    if database.find_user(user_id=message.from_user.id) is not None:
        if pos == 14:
            if len(splitted) < 2 or len(splitted) > 3:
                bot.send_message(chat_id=message.from_user.id,
                                 text='Введено некорректно')
                bot.send_message(chat_id=message.from_user.id,
                                 text='Введите ФИО прогулявших')
                database.update_position(message.from_user.id, 14)
            bot.send_message(chat_id=message.from_user.id,
                             text='Прогульщики будут гореть в аду')
            database.update_position(message.from_user.id, 14)
            # тут splitted[0] фамилия splitted[1] имя отчесвто
        elif pos == 102:
            global task_description, max_mark
            s = ''
            max_mark = splitted.pop()
            for i in splitted:
                s += i + ' '
            task_description = s
            markup = telebot.types.ReplyKeyboardMarkup(True, False)
            markup.row('Да')
            markup.row('Нет')
            if max_mark.isdigit():
                bot.send_message(message.chat.id,
                                 "Домашнее задание: {}\nМакс. балл {}".format(s, max_mark), reply_markup=markup)
                database.update_position(message.from_user.id, 102)
            else:
                bot.send_message(message.chat.id,
                                 "Введите дз, последним должен быть макс.балл!", reply_markup=markup)
        elif pos == 12:
            global post_text
            post_text = message.text
            markup = telebot.types.ReplyKeyboardMarkup(True, False)
            markup.row('Да')
            markup.row('Нет')
            bot.send_message(message.from_user.id,
                             'Отправить всем следующее:\n{}'.format(post_text), reply_markup=markup)
    else:
        if message.from_user.id in pos_for_none.keys():
            if pos_for_none[message.from_user.id] == 31:
                if len(splitted) < 3 or len(splitted) > 4:
                    bot.send_message(chat_id=message.from_user.id,
                                     text='Введено некорректно')
                    keyboard.display_nomer_zachetki(message)
                else:
                    is_number = splitted[0]
                    if not is_number:
                        bot.send_message(chat_id=message.from_user.id,
                                         text='Номер зачетки введён некорректно!')
                        keyboard.display_nomer_zachetki(message)
                    else:
                        record = splitted[0]
                        splitted.pop(0)
                        if len(splitted) == 3:
                            name = splitted[1]
                            surname = splitted[0]
                            midname = splitted[2]
                            FIO = '{} {} {} '.format(name, surname, midname)
                            dict_for_none.update({message.from_user.id:
                                                      student(name, surname, midname, int(record))})
                        else:
                            name = splitted[1]
                            surname = splitted[0]
                            midname = None
                            FIO = '{} {}  '.format(name, surname)
                            dict_for_none.update({message.from_user.id:
                                                      student(name, surname, midname, int(record))})
                        keyboard.display_proverka(message, record, FIO)
                        pos_for_none[message.from_user.id] = 32
            else:
                pos_for_none[message.from_user.id] = 3
                keyboard.display_start(message)
        else:
            pos_for_none.update({message.from_user.id: 3})
            keyboard.display_start(message)


@server.route('/' + TOKEN, methods=['POST'])
def get_message():
    if database.connection.closed == 1:
        open_conn(database)
        time.sleep(2)
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://work-with-course.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server = Flask(__name__)
    database = db.Connection()
    scheduler = BackgroundScheduler()
    open_conn(database)
    scheduler.start()
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
