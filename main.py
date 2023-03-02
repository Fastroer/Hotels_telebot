import telebot
import sqlite3
import requests
import datetime
import os
from telebot import types
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)



def connection_to_BD():
    """Connects to the SQLite database 'sql_hotels_settings.db' and returns the connection and cursor objects.

    Returns:
    conn: sqlite3.Connection
    A connection object for the SQLite database.

    cursor: sqlite3.Cursor
    A cursor object for executing SQL statements on the SQLite database.
    """
    conn = sqlite3.connect('sql_hotels_settings.db')
    cursor = conn.cursor()
    return conn, cursor


def disconnection_from_BD(conn):
    """Commits any pending transactions and closes the connection to the SQLite database.

    Parameters:
    conn: sqlite3.Connection
    A connection object for the SQLite database to be closed.
    """
    conn.commit()
    conn.close()


@bot.message_handler(commands=['start'])
def start(message):
    """Handles the '/start' command sent by the user and sends a message with a keyboard markup.

    Parameters:
    message: telegram.Message
    A message object representing the message sent by the user to the bot.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton("👋 Поздороваться")
    btn2 = types.KeyboardButton("🏨 Выбор отеля")
    btn3 = types.KeyboardButton("📄 История поиска")
    btn4 = types.KeyboardButton("/help")
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(message.chat.id,
                     text="Привет, {0.first_name}! Я бот, который поможет тебе с выбором отелей по всему миру!".format(
                         message.from_user), reply_markup=markup)

@bot.message_handler(commands=['history'])
def search_history_handler(message):
    """Handles the '/history' command sent by the user and sends a message
    containing the user's search history from the database.

    Parameters:
    message: telegram.Message
    A message object representing the message sent by the user to the bot.
    """
    date_today = datetime.datetime.now().strftime("%d-%d-%Y")
    user_ID = message.chat.id
    data_bd = search_settings_bd(message)

    hotels_set = (f'Количество отелей: {data_bd[3]}:\n'
                  f'Название города: {data_bd[1]}\n'
                  f'Минимальная цена: {data_bd[11]}\n'
                  f'Максимальная цена: {data_bd[12]}\n'
                  f'Максимальная дистанция: {data_bd[13]}\n'
                  f'Фильтр: {data_bd[2]}\n'
                  f'Нужны ли фото: {data_bd[14]}\n'
                  f'День заселения: {data_bd[4]}\n'
                  f'Месяц заселения: {data_bd[5]}\n'
                  f'Год заселения: {data_bd[6]}\n'
                  f'День выселения: {data_bd[7]}\n'
                  f'Месяц выселения: {data_bd[8]}\n'
                  f'Год выселения: {data_bd[9]}\n')

    conn, cursor = connection_to_BD()
    cursor.execute("SELECT hotels FROM Hotels_history WHERE user_id=?", (message.chat.id,))

    data_bd = cursor.fetchall()
    result_str = ('\n'.join([f'{i + 1}. {data[0]}' for i, data in enumerate(data_bd)]))

    bot.send_message(message.chat.id, f'Дата: {date_today}\n'
                                      f'Ваш id: {user_ID}\n'
                                      f'Параметры для последнего поиска:\n {hotels_set}\n'
                                      f'Список последних выведеных вам отелей:\n {result_str}\n')
    result_str = ""


def search_settings_bd(message):
    """Retrieve the user's hotel search settings from the database.

        Args:
            message: A message object that contains the user's ID.

        Returns:
            A tuple of the user's hotel search settings, or None if the settings do not exist in the database.
    """
    conn, cursor = connection_to_BD()
    cursor.execute(
        "SELECT user_ID, city_name, filtering_method, number_hotels,"
        " checkin_day, checkin_month, checkin_year, checkout_day,"
        " checkout_month, checkout_year, city_ID, min_price,"
        " max_price, max_dist, photos_choice"
        " FROM Hotels_settings WHERE user_ID = ?",
        (message.chat.id,))

    data_bd = cursor.fetchone()

    if data_bd:
        disconnection_from_BD(conn)
        return data_bd
    else:
        disconnection_from_BD(conn)
        return None


def response_hotels(message):
    """Retrieve and send hotel search results to the user based on the user's search settings.

    Args:
        message: A message object that contains the user's ID.

    Returns:
        None
    """
    try:
        conn, cursor = connection_to_BD()
        cursor.execute("DELETE FROM Hotels_history WHERE user_ID = ?", (message.chat.id,))

        chat_id = message.chat.id
        bot.send_message(message.chat.id, 'Одну секунду, идет поиск отелей...')

        url_list = "https://hotels4.p.rapidapi.com/properties/v2/list"
        url_id = "https://hotels4.p.rapidapi.com/locations/v3/search"

        headers = {
            "content-type": os.getenv('CON_TYPE'),
            "X-RapidAPI-Key": os.getenv('XRAPI-Key'),
            "X-RapidAPI-Host": os.getenv('XRAPI-Host')
        }

        cursor.execute("SELECT city_name FROM Hotels_settings WHERE user_ID = ?", (message.chat.id,))

        data_bd_name = cursor.fetchone()

        querystring = {"q": data_bd_name[0], "locale": "ru_RU", "langid": "1033", "siteid": "300000001"}
        response_id = requests.request("GET", url_id, headers=headers, params=querystring)
        if response_id == "<Response [204]>":
            bot.send_message(message.chat.id, f'Извините, произошла ошибка. '
                                              f'Пожалуйста, убедитесь в правильности введенного названия города и повторите попытку.')
        data_id = response_id.json()
        for item in data_id['sr']:
            if 'gaiaId' in item:
                city_id = (item['gaiaId'])
                cursor.execute("UPDATE Hotels_settings SET city_ID=?  WHERE user_ID=?",
                               (city_id, message.chat.id))
                break
            elif 'hotelId' in item:
                if 'cityId' in item:
                    city_id = (item['cityId'])
                    cursor.execute("UPDATE Hotels_settings SET city_ID=?  WHERE user_ID=?",
                                   (city_id, message.chat.id))
                    break
            else:
                bot.send_message(message.chat.id, 'К сожалению, для данного города невозможно найти доступные отели. '
                                                  'Рекомендуется попробовать поискать в более крупном городе, '
                                                  'где возможно будет больше вариантов размещения.')
        disconnection_from_BD(conn)

        data_bd = search_settings_bd(message)
        number_hotels = data_bd[3]

        payload = {
            "currency": "USD",
            "eapid": 1,
            "locale": "ru_RU",
            "siteId": 300000001,
            "destination": {"regionId": data_bd[10]},
            "checkInDate": {
                "day": int(data_bd[4]),
                "month": int(data_bd[5]),
                "year": int(data_bd[6])
            },
            "checkOutDate": {
                "day": int(data_bd[7]),
                "month": int(data_bd[8]),
                "year": int(data_bd[9])
            },
            "rooms": [{"adults": 1}],
            "resultsStartingIndex": 0,
            "resultsSize": 200,
            "sort": data_bd[2],
            "filters": {}
        }
        if data_bd[2] == 'GUEST_RATING':
            payload["filters"] = {"price": {
                "max": int(data_bd[12]),
                "min": int(data_bd[11])
            }}
        else:
            payload["filters"] = {}

        response_list = requests.request("POST", url_list, json=payload, headers=headers)

        if response_list == "<Response [204]>":
            bot.send_message(message.chat.id, f'Извините, произошла ошибка. '
                                              f'Пожалуйста, убедитесь в правильности введенных параметров и повторите попытку.')

        data_list = response_list.json()

        index = None
        for index in range(len(data_list['data']['propertySearch']['properties'])):
            if index > (number_hotels - 1):
                break
            photo_url = data_list['data']['propertySearch']['properties'][index]['propertyImage']['image']['url']

            name = data_list['data']['propertySearch']['properties'][index]['name']

            grade = data_list['data']['propertySearch']['properties'][index]['reviews']['score']
            grades_users = data_list['data']['propertySearch']['properties'][index]['reviews']['total']

            address = data_list['data']['propertySearch']['properties'][index]['neighborhood']['name']

            price = data_list['data']['propertySearch']['properties'][index]['price']['options'][0]['formattedDisplayPrice']

            price_all = data_list['data']['propertySearch']['properties'][index]['price']['displayMessages'][1]['lineItems'][0]['value']

            distance = data_list['data']['propertySearch']['properties'][index]['destinationInfo']['distanceFromDestination']['value']

            if data_bd[2] == 'GUEST_RATING':
                if float(distance) > float(data_bd[13]):
                    number_hotels += 1
                    break

            if data_bd[14] == '1':
                hotels = (f'Отель номер {index + 1}:\n'
                          f'Название отеля: {name}\n'
                          f'Оценка пользователей: {grade}/10. Количество оценок: {grades_users}\n'
                          f'Цена за ночь: {price}\n'
                          f'Цена за все время: {price_all}\n'
                          f'Адрес: {address}\n'
                          f'Дистанция до центра города: {distance} км\n')
                bot.send_photo(chat_id, photo_url, caption=hotels)
            else:
                hotels = (f'Отель номер {index + 1}:\n'
                          f'Название отеля: {name}\n'
                          f'Оценка пользователей: {grade}/10. Количество оценок: {grades_users}\n'
                          f'Цена за ночь: {price}\n'
                          f'Цена за все время: {price_all}\n'
                          f'Адрес: {address}\n'
                          f'Дистанция до центра города: {distance} км\n')

                bot.send_message(message.chat.id, hotels)

            today = datetime.date.today()
            conn, cursor = connection_to_BD()
            cursor.execute("INSERT INTO Hotels_history (user_ID, date_responce, hotels) "
                           "VALUES (?, ?, ?)",
                           (message.chat.id, today, hotels))
            disconnection_from_BD(conn)
        if index < number_hotels - 1:
            bot.send_message(message.chat.id,
                             f'Извините, по запрашиваемым параметрам нам не удалось найти достаточное '
                             f'количество отелей в данном городе. '
                             f'Рекомендуется изменить параметры поиска, '
                             f'возможно это позволит найти больше вариантов отелей.')


    except (TypeError, NameError, KeyError, requests.exceptions.RequestException, IndexError, AttributeError, ValueError):
        bot.send_message(message.chat.id, f'Извините, произошла ошибка. '
                                          f'Пожалуйста, убедитесь в правильности введенных параметров и повторите попытку.')
    finally:
        return bot.send_message(message.chat.id,
                         f'Чтобы повторно найти отели, вы можете открыть клавиатуру с выбором действий, нажав на соответствующую кнопку.')


def price_range(message):
    """Ask the user to enter the minimum and maximum hotel price range in USD
    and register the next step handler to process the input.

    Args:
    - message: Message object representing the message sent by the user.

    Returns:
    None
    """
    bot.send_message(message.chat.id, "Введите минимальную и максимальную стоимость отеля в долларах США (например, '100 200'): ")
    bot.register_next_step_handler(message, process_price_range)


def process_price_range(message):
    """Process the user's input of minimum and maximum hotel price range, validate the input,
    update the database with the values, and ask the user to input the maximum distance to city center in kilometers.

    Args:
    - message: Message object representing the message sent by the user.

    Returns:
    None
    """
    try:
        min_price, max_price = message.text.split()
        min_price = int(min_price)
        max_price = int(max_price)
        if min_price < 0 or max_price < 0:
            raise ValueError
        if min_price >= max_price:
            raise ValueError

        conn, cursor = connection_to_BD()
        cursor.execute("UPDATE Hotels_settings SET min_price=?, max_price=? WHERE user_ID=?",
                       (min_price, max_price, message.chat.id))
        disconnection_from_BD(conn)

        bot.send_message(message.chat.id, f"Вы ввели минимальную стоимость {min_price} и максимальную стоимость {max_price}.")
        msg = bot.send_message(message.chat.id, "Введите максимальную дистанцию до центра города от отеля в километрах (например, '10').")
        bot.register_next_step_handler(msg, process_center_distance)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Введите диапазон цен в правильном формате (например, '100 200') и убедитесь, что первое число меньше второго и они больше, или равны нулю.")
        bot.register_next_step_handler(msg, process_price_range)


def process_center_distance(message):
    """Process the user's input of the maximum distance to city center,
    validate the input, update the database with the value,
    and call the number_hotels_1 function to display the number of hotels that meet the user's criteria.

    Args:
    - message: Message object representing the message sent by the user.

    Returns:
    None
    """
    try:
        distance = int(message.text)
        if distance > 0:
            conn, cursor = connection_to_BD()
            cursor.execute("UPDATE Hotels_settings SET max_dist=?  WHERE user_ID=?",
                           (distance, message.chat.id))
            disconnection_from_BD(conn)

            bot.send_message(message.chat.id, f"Вы ввели дистанцию до центра города {distance} км.")
            number_hotels_1(message)
        else:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "Произошла ошибка, убедитесь, что вы ввели максимальную дистанцию в километрах до центра города от отеля правильно (например, '10').")
        bot.register_next_step_handler(msg, process_center_distance)


def period_in_hotel(message):
    """Ask the user to select the check-in and check-out dates using an inline keyboard.

    Args:
    - message: Message object representing the message sent by the user.

    Returns:
    None
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    checkin_button = types.InlineKeyboardButton("Дата заселения", callback_data='checkins')
    checkout_button = types.InlineKeyboardButton("Дата выселения", callback_data='checkouts')
    markup.add(checkin_button, checkout_button)
    bot.send_message(message.chat.id, "Выберите дату заселения и выселения:", reply_markup=markup)


def process_checkin(message):
    """Process the user's input of the check-in date, validate the input, update the database with the value,
    and ask the user to input the check-out date. If both dates have been entered,
    call the response_hotels function to display the available hotels.

    Args:
    - message: Message object representing the message sent by the user.

    Raises:
    ValueError: If the date entered is not in the correct format.

    Returns:
    None
    """
    try:
        date_obj = datetime.datetime.strptime(message.text, '%d.%m.%Y').date()
        day = date_obj.strftime('%d').replace('0', '')
        month = date_obj.strftime('%m').replace('0', '')

        conn, cursor = connection_to_BD()
        cursor.execute("SELECT last_step FROM Hotels_settings WHERE user_ID=?", (message.chat.id,))
        last_step = cursor.fetchone()[0]

        if last_step == 0 or last_step == None:
            cursor.execute("UPDATE Hotels_settings SET checkin_day=?, checkin_month=?, checkin_year=?, last_step=1 WHERE user_ID=?",
                           (day, month, date_obj.strftime('%Y'), message.chat.id))
            bot.send_message(message.chat.id, "Дата заселения сохранена")
            disconnection_from_BD(conn)

        elif last_step == 1:
            cursor.execute("UPDATE Hotels_settings SET checkout_day=?, checkout_month=?, checkout_year=?, last_step=0 WHERE user_ID=?",
                           (day, month, date_obj.strftime('%Y'), message.chat.id))
            bot.send_message(message.chat.id, "Дата заселения сохранена")
            disconnection_from_BD(conn)
            response_hotels(message)

    except ValueError:
        bot.send_message(message.chat.id, "Введите дату в правильном формате (ДД.ММ.ГГГГ)")
        bot.register_next_step_handler(message, process_checkout)


def process_checkout(message):
    """Processes the checkout date entered by the user, and updates the checkout date in the database.
    If both dates have been entered, call the response_hotels function to display the available hotels.

    Args:
        message: A message object containing the user's input.

    Returns:
        None.
    """
    try:
        date_obj = datetime.datetime.strptime(message.text, '%d.%m.%Y').date()
        day = date_obj.strftime('%d').replace('0', '')
        month = date_obj.strftime('%m').replace('0', '')

        conn, cursor = connection_to_BD()
        cursor.execute("SELECT last_step FROM Hotels_settings WHERE user_ID=?", (message.chat.id,))
        last_step = cursor.fetchone()[0]

        if last_step == 0 or last_step == None:
            cursor.execute(
                "UPDATE Hotels_settings SET checkin_day=?, checkin_month=?, checkin_year=?, last_step=1 WHERE user_ID=?",
                (day, month, date_obj.strftime('%Y'), message.chat.id))
            bot.send_message(message.chat.id, "Дата выселения сохранена")
            disconnection_from_BD(conn)

        elif last_step == 1:
            cursor.execute(
                "UPDATE Hotels_settings SET checkout_day=?, checkout_month=?, checkout_year=?, last_step=0 WHERE user_ID=?",
                (day, month, date_obj.strftime('%Y'), message.chat.id))
            bot.send_message(message.chat.id, "Дата выселения сохранена")
            disconnection_from_BD(conn)
            response_hotels(message)

    except ValueError:
        bot.send_message(message.chat.id, "Введите дату в правильном формате (ДД.ММ.ГГГГ)")
        bot.register_next_step_handler(message, process_checkout)


def number_hotels_1(message):
    """Ask the user for the number of hotel options they would like to receive.

    Args:
        message: A telegram message object.

    Returns:
        None.
    """
    bot.send_message(message.chat.id, 'Сколько вариантов отелей вы бы хотели получить? ')

    def number_hotels_2(message):
        """Update the number of hotel options in the database and ask the user if they want to see hotel photos.

        Args:
            message: A telegram message object.

        Raises:
            ValueError: If the number entered is not an integer.

        Returns:
            None.
        """
        try:

            number_hotels = int(message.text)
            if number_hotels > 25 or number_hotels < 0:
                bot.send_message(message.chat.id, 'Выставлено максимальное значение: 25')
                conn, cursor = connection_to_BD()
                cursor.execute("UPDATE Hotels_settings SET number_hotels=? WHERE user_ID=?",
                               (25, message.chat.id))
                disconnection_from_BD(conn)
            else:
                conn, cursor = connection_to_BD()
                cursor.execute("UPDATE Hotels_settings SET number_hotels=? WHERE user_ID=?",
                               (number_hotels, message.chat.id))
                disconnection_from_BD(conn)

            keyboard_choice = types.InlineKeyboardMarkup(row_width=2)
            keyboard_choice.add(types.InlineKeyboardButton(text="Да", callback_data='yes'))
            keyboard_choice.add(types.InlineKeyboardButton(text="Нет", callback_data='no'))

            bot.send_message(message.chat.id, 'Желаете видеть фотографии отелей? ', reply_markup=keyboard_choice)
        except ValueError:
            msg = bot.send_message(message.chat.id,
                                   "Произошла ошибка. Повторно введите ответ и убедитесь, что вы ввели число.")
            bot.register_next_step_handler(msg, number_hotels_1)

    bot.register_next_step_handler(message, number_hotels_2)


def main_function(message):
    """Handles the main hotel search functionality. Stores user's preferred city and filtering method in the database.
    Allows user to choose from a set of filtering options through an inline keyboard markup. Also handles callbacks for
    updating the database with the user's selected filters, as well as for getting the check-in and check-out dates from
    the user.

    Args:
        message (telegram.Message): Message object representing the user's input message.

    Returns:
        None
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(types.InlineKeyboardButton(text="/lowprice", callback_data='PRICE_LOW_TO_HIGH'))
    keyboard.add(types.InlineKeyboardButton(text="/bestdeal", callback_data='GUEST_RATING'))
    keyboard.add(types.InlineKeyboardButton(text="/highprice", callback_data='PRICE_HIGH_TO_LOW'))

    bot.send_message(message.chat.id, f'Поиск будет выполнен в городе: {message.text}')
    conn, cursor = connection_to_BD()
    cursor.execute("SELECT COUNT(*) FROM Hotels_settings WHERE user_ID=?", (message.chat.id,))
    data = cursor.fetchone()
    if data[0] == 0:
        cursor.execute("INSERT INTO Hotels_settings (city_name, user_ID) VALUES (?, ?)",
                       (message.text, message.chat.id))
    else:
        cursor.execute("UPDATE Hotels_settings SET city_name=? WHERE user_ID=?", (message.text, message.chat.id))
    disconnection_from_BD(conn)

    bot.send_message(message.chat.id, 'Выберите критерий по которому будут фильтроваться отели: ',
                     reply_markup=keyboard)
    already_chosen = False

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        nonlocal already_chosen

        if not already_chosen and call.data in ['PRICE_LOW_TO_HIGH', 'PRICE_HIGH_TO_LOW', 'GUEST_RATING']:
            choice = call.data
            conn, cursor = connection_to_BD()
            cursor.execute("UPDATE Hotels_settings SET filtering_method=?, max_dist=?, min_price=?, max_price=? WHERE user_ID=?",
                           (choice, None, None, None, message.chat.id))
            disconnection_from_BD(conn)
            if choice == 'GUEST_RATING':
                price_range(message)
            else:
                number_hotels_1(message)
            already_chosen = True

        elif call.data == 'yes' or call.data == 'no':
            conn, cursor = connection_to_BD()
            if call.data == 'yes':
                cursor.execute("UPDATE Hotels_settings SET photos_choice=? WHERE user_ID=?",
                               (True, message.chat.id))
            elif call.data == 'no':
                cursor.execute("UPDATE Hotels_settings SET photos_choice=? WHERE user_ID=?",
                               (False, message.chat.id))
            disconnection_from_BD(conn)
            period_in_hotel(message)
            already_chosen = False


        elif call.data == "checkins":
            bot.send_message(call.message.chat.id, "Введите дату заселения в формате ДД.ММ.ГГГГ:")
            bot.register_next_step_handler(call.message, process_checkin)
        elif call.data == "checkouts":
            bot.send_message(call.message.chat.id, "Введите дату выселения в формате ДД.ММ.ГГГГ:")
            bot.register_next_step_handler(call.message, process_checkout)


@bot.message_handler(content_types=['text'])
def func(message):
    """Handles user input messages, and responds accordingly based on the message text.

    Args:
        message (telegram.Message): Message object representing the user's input message.

    Returns:
        None
    """
    if (message.text == "👋 Поздороваться"):
        bot.send_message(message.chat.id, text="Привет,я бот Альфред! 😊")

    elif (message.text == "/start"):
        start(message)

    elif (message.text == "📄 История поиска"):
        search_history_handler(message)

    elif (message.text == "🏨 Выбор отеля"):
        city_func = bot.send_message(message.chat.id, text="Введите город в котором будем искать отели")
        bot.register_next_step_handler(city_func, main_function)

    elif (message.text == "/help"):
        bot.send_message(message.chat.id,
                         text="Для вашего удобства, вот список команд, которыми располагает бот Альбер:"
                              "\n📄 История поиска -  данная команда позволяет получить список использованных вами команд в определенном временном промежутке."
                              "\n👋 Поздороваться - данная команда позволяет вам поздороваться с ботом!"
                              "\n🏨 Выбор отеля - данная команда позволяет вам найти отель в необходимом городе:"
                              "\n   /lowprice - использование данной команды предоставляет список самых доступных отелей в заданном городе;"
                              "\n   /highprice - использование данной команды предоставляет список наиболее дорогих отелей в заданном городе;"
                              "\n   /bestdeal - использование данной команды предоставляет список отелей, соответствующих вашим заданным критериям;")
    else:
        bot.send_message(message.chat.id, text="На такую команду я не запрограммировал...")


bot.polling(none_stop=True)