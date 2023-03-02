# Hotel Search Bot
https://t.me/PlanetHotelExplorer_bot
This is a Telegram bot that allows users to search for hotels in a particular city and filter the search results based on various criteria.

# How to Use

How to Use:
1. Start the conversation with the bot by sending the /start command.
2. Choose the "🏨 Выбор отеля" option to find hotels in a specific city.
3. Enter the name of the city you want to search for.
4. Choose the criteria to filter the search results.
5. Optionally, choose whether you want to see hotel photos and enter the check-in and check-out dates.
6. The bot will display a list of hotels that match your search criteria.
7. If you want to view your search history, send the "📄 История поиска" command.
8. If you want to say hello to the bot, send the "👋 Поздороваться" command.
9. If you need help using the bot, send the /help command.

📄 История поиска:

You can view your search history by sending the /history command. The bot will send you a list of your previous requests that you made to the bot.

👋 Поздороваться:

If you want to say hello to the bot, send the /hello command. The bot will respond with a welcoming message.

/help Command:

If you need help using the bot, send the /help command. The bot will send you a list of available commands and a brief description of what they do.

# Technical Details

The bot is written in Python using the Telegram Bot API and the SQLite database. It uses the python-telegram-bot library to interact with the Telegram Bot API and the sqlite3 library to interact with the database.

The bot consists of two main functions:

    1. main_function(message): This function handles the hotel search and filtering based on the user's input.

    2. func(message): This function handles the other commands and messages that the user sends to the bot.

The bot also uses several helper functions to interact with the database and perform various tasks such as sending messages, processing dates, and handling user input.

# How to Run

To run the bot, you will need to:
1. Clone this repository to your local machine.
2. Install the required dependencies using pip install -r requirements.txt.
3. Create a new bot on Telegram and obtain the API token.
4. Create a new SQLite database.
5. Modify the config.py file to include your API token and database information.
6. Run the bot using python main.py.

# Future Improvements

Some potential improvements to the bot could include:
1. Adding more filtering criteria for hotel search results.
2. Improving the user interface and adding more interactive elements.
3. Adding support for multiple languages.
4. Adding support for searching for flights and other travel-related information.