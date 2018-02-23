'''
INF510 - Homework 5 
Adam Vaccaro
Purpose: Create SQL tables and add meta data
'''
# Import packages, libraries, and modules:
import os
# Import necessary SQL alchemy commands:
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
# Import SQL table definitions
#import table_definitions
from table_definitions import Base, engine
from table_definitions import Exchange, Coin, Market, Bitcointalk_Thread
from table_definitions import ABS_DB_PATH
# Import API accessors and webscraper:
import bittrex_api
import coinmarketcap_api
import bitcointalk_scraper
# Import datetime:
from datetime import datetime

# Database names:
DB_FILE_NAME = 'crypto.db'
#DB_SQLITE_NAME = 'sqlite:///crypto.db'
DB_SQLITE_NAME = ABS_DB_PATH
# Database engine:
DB = engine #from table_definitions.py

# Check to see if DB already exists in current directory:
cwd = os.getcwd() #current working directory
# Prepare console messages:
checking_msg = '''
Checking to see if database exists in current dictory.
Database file name:
%s \n
Current dictory:
%s \n
''' % (DB_FILE_NAME, cwd)
exists_msg = '''
Database already exists in storage.
Re-initializing database will erase all data in DB.
Are you sure you want to proceed? (yes/no)
'''
reinitialize_msg = '''
You have chosen to reinitialize the database.
Existing DB file will now be erased from disk storage.
'''
no_initialize_msg = '''
You have chosen not to reinitialize the database.
Existing DB file will remain on disk storage.
This script will now end.
'''
invalid_response_msg = '''
You entered an invalid response.
(Your response: %s)
''' 
print(checking_msg)
for file in os.listdir():
	already_exists = file == DB_FILE_NAME
	if already_exists:
		invalid_input_flag = True
		while invalid_input_flag:
			str_in = str(input(exists_msg))
			low_str_in = str_in.lower()
			if low_str_in == 'yes':
				invalid_input_flag = False
				print(reinitialize_msg)
				os.remove(DB_FILE_NAME)
			elif low_str_in == 'no':
				print(no_initialize_msg)
				exit()
			else:
				print(invalid_response_msg % str_in)

# Create all tables:
Base.metadata.create_all(engine)

# create a Session:
Session = sessionmaker(bind=engine)
session = Session()

# Prepare exchange metadata
# Bittrex:
bittrex_exchange = Exchange(
	exchange_name = 'Bittrex',
	exchange_url = 'https://bittrex.com/'
)
# Add exchange to DB
session.add(bittrex_exchange)
session.commit()

# Add bitcoin Coin metadata and initial tricker to DB:
bitcoin_data = coinmarketcap_api.access_api('bitcoin')

# Prepare get alt Coin metadata and add initial ticker data from Coinmarketcap:
altcoins = ['litecoin', 'ethereum', 'neo']
for coin in altcoins:
	coin_data = coinmarketcap_api.access_api(coin)
	coin_symbol = coin_data['symbol']
	# Add all BTC-altcoin markets:
	market_data = bittrex_api.access_api(coin_symbol)

# Initialize Bitcointalk data by scraping entire board:
bitcointalk_scraper.scrape_threads('end')

# Prepare finish text
finish_msg = '''
*** SQLite database has been created ***
Metadata for coins, exchanges, markets, and all forum threads have been added
to database.  Time stamped ticker price and thread view/replies counts data
have been entered into database.
'''
path_msg = '''
Name of SQLite database file:
%s

Path to SQLite database file:
%s
''' 
# Prepare DB file path string (if possible):
if '/'  in cwd: 
	db_file_path = cwd + '/' + DB_FILE_NAME
	path_flag = True
elif '\\'  in cwd: 
	db_file_path = cwd + '\\'+ DB_FILE_NAME
	path_flag = True
else: path_flag = False
# Print finish message
print(finish_msg)
if path_flag: print(path_msg % (DB_FILE_NAME, db_file_path))