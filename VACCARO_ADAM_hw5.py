''' VACCARO_ADAM_hw5.py
Adam Vaccaro
INF510 - Dr. Jeremy Abramson
USC - Fall 2017

Purpose: 
First check to see if DB exists in current directory, if not, offer to
initialize the DB (this requires 2-3 minutes on a decent internet connection).
Then, retrieve data from all three data sources with ability to specify
retrieval from online sources or from local storage.  Next, find the Altcoin
that shows the largest difference in price according to Bittrex.com and
Coinmarketcap.com.  Finally, find the most recent Bitcointalk forum post on a
thread that contains the name of the Altcoin in its subject and return its URL.

If local:
The data will be retrieved from the SQLite database and the price difference
will be calculated using the most recent ticker data entries in the database.
The script will then return the URL of the most recent Bitcointalk post found
in the local database.

If remote:
First, live ticker prices will be retrieved from Bittrex and Coinmarketcap via
API and stored in the local SQLite DB.  Then, the script will retrieve the time 
of the most recent post recorded in local DB and scrape the Bitcointalk forum
threads for posts more recent than that.  It will add any new threads to the
thread metadata table, and add time stamped view/reply data for all updated
posts.  The script will then retrieve the current ticker prices from the local
DB and calculate which coin has the largest difference.  It will search for the 
most recent post relevant to the coin in the updated local DB.

Outputs:
The largest price difference found, the coin with the largest difference,
and URL to the most recent forum post related to that coin.

Input syntax:
python VACCARO_ADAM_hw5.py -source=local
python VACCARO_ADAM_hw5.py -source=remote

'''
# Import packages, libraries, and modules:
import os, sys
# Import necessary SQL alchemy commands:
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
# Import SQL table definitions
from table_definitions import Base, engine
from table_definitions import Exchange, Coin, Market 
from table_definitions import Bitcointalk_Thread, Bitcointalk_Count
from table_definitions import Bittrex_Ticker, Coinmarketcap_Ticker
from table_definitions import project_root
# Import API/webscraper from previous assignment
#bittrex_api, coinmarketcap_api, and bitcointalk_scraper accessed via HW4:
import VACCARO_ADAM_hw4 as HW4
# Import datetime:
from datetime import datetime

# Database name:
DB_FILE_NAME = 'crypto.db' 
DB_SQLITE_NAME = 'sqlite:///crypto.db'
# Database engine:
DB = engine #from table_definitions

# Prepare console messages for DB check:
checking_msg = '''
Checking to see if database exists in current dictory...\n
Database file name: \n%s\n
Current dictory:\n%s
'''
found_msg = '''
Database was found in current directory.  
Script will now proceed.
'''
not_found_msg = '''
Database was not found in current dictory.  Script cannot proceed without
the database in local storage.  Initializing the database  will create the DB 
and populate it with metadata and data entries.  The process requires being
connected to the internet and will take several minutes.
Would you like to proceed? (yes/no)
'''
initialize_msg = '''
You have chosen to initialize the database.
Initialization process will now begin.
'''
no_initialize_msg = '''
You have chosen not to reinitialize the database.
No database file will be created on disk storage.
This script will now end.
'''
invalid_response_msg = '''
You entered an invalid response.
Please enter 'yes' or 'no'.
(Your response: %s)
''' 


def check_db_exists():
	'''
	Check to see if SQLite DB exists in local storage.
	If not, offer the user to initialize the DB.
	If DB is not found and user does not want to initialize DB, end script.
	'''
	# Check to see if DB  exists in current directory:
	#cwd = os.getcwd() #current working directory
	#cwd = '/Users/ADV/Documents/INF510/Final'
	#project_root = os.path.dirname(os.path.abspath(__file__))
	#print(checking_msg % (DB_FILE_NAME, cwd))
	print(checking_msg % (DB_FILE_NAME, project_root))
	#already_exists = DB_FILE_NAME in os.listdir()
	#already_exists = DB_FILE_NAME in os.listdir(cwd)
	already_exists = DB_FILE_NAME in os.listdir(project_root)
	if not already_exists:
		invalid_input_flag = True
		while invalid_input_flag:
			str_in = str(input(not_found_msg))
			low_str_in = str_in.lower()
			if low_str_in == 'yes':
				invalid_input_flag = False
				print(initialize_msg)
				import initialize_sql_db		
			elif low_str_in == 'no':
				print(no_initialize_msg)
				exit()
			else:
				print(invalid_response_msg % str_in)
	elif already_exists:
		print(found_msg) 


def get_live_data_from_web(coin_tups):
	'''
	Retrieve data from web sources using API/webscraper from HW4:
	'''
	for coin_tup in coin_tups:
		# Extract name and symbol from tuple:
		coin_name = coin_tup[0]
		coin_symbol = coin_tup[1]
		# First get live coin ticker prices from coinmarket and add to DB:
		HW4.main('coinmarketcap', [coin_name]) #coinmarketcap_api.access_api(coin_name)
		if coin_symbol != 'BTC': # For non-BTC coins
			# Get live market prices from Bittrex and add to DB:
			HW4.main('bittrex', [coin_symbol]) #bittrex_api.access_api(coin_symbol)
	# Now scrape Bitcointalk forum and add new threads/posts to DB:
	HW4.main('bitcointalk', ['last']) #bitcointalk_scraper.scrape_threads()


def find_largest_difference(altcoin_tups):
	'''
	Find largest price difference between Coinmarketcap and Bittrex ticker
	prices.  
	'''
	# Create a session:
	Session = sessionmaker(bind=engine)
	session = Session()
	largest_difference = 0 # initialize largest difference at 0
	for altcoin in altcoin_tups:
		coin_name = altcoin[0] #get coin name from tuple
		# Find coin in DB and retrieve ID to use as foreign key:
		coin = session.query(Coin).filter(Coin.coin_name == coin_name).first()
		coin_fid = coin.id
		# Get most recently entered coin ticker price from DB:
		coin_ticker_query = session.query(Coinmarketcap_Ticker)
		coin_ticker_filter = coin_ticker_query.filter(
			Coinmarketcap_Ticker.coin_id == coin_fid
		)
		last_coin_ticker = coin_ticker_filter.order_by(
			Coinmarketcap_Ticker.last_updated.desc()
		).first()
		# Get  ticker price and reverse integer conversion:
		last_coin_price = last_coin_ticker.price_btc
		# Find matching market and retrieve market ID to use as foreign key:
		market_query = session.query(Market)
		market = market_query.filter(Market.coin2_id == coin_fid).first()
		market_fid = market.id
		# Get most recently entered market ticker price from DB:
		market_ticker_query = session.query(Bittrex_Ticker)
		market_filter = market_ticker_query.filter(
			Bittrex_Ticker.market_id == market_fid
		)
		last_market_ticker = market_filter.order_by(
			Bittrex_Ticker.timestamp.desc()
		).first()
		last_market_price = last_market_ticker.last_price
		# Calculate price difference and update largest price (if necessary):
		price_difference = abs(last_coin_price - last_market_price)
		if price_difference > largest_difference: 
			largest_difference = price_difference
			# Store info for largest coin:
			largest_tup = altcoin
	return([largest_difference, largest_tup])

def find_most_recent_thread(coin_tup):
	'''
	Find most recent thread for a given coin.

	'''
	# Extract coin name and symbol from coin tuple:
	[name, symbol] = coin_tup[:2]
	# Find most recent thread counts in DB:
	count_query = session.query(Bitcointalk_Count)
	recent_counts = count_query.order_by(
		Bitcointalk_Count.last_post_datetime.desc()
	)
	recent_ids = [count.thread_id for count in recent_counts]
	# Query threads:
	thread_query = session.query(Bitcointalk_Thread)
	# Find thread subjects that are like the name:
	like_name = thread_query.filter(
		Bitcointalk_Thread.thread_subject.like('%'+name+'%')
	).all()
	like_name_ids = [thread.id for thread in like_name]
	# Find thread subjects that are like the symbol:
	like_symbol = thread_query.filter(
		Bitcointalk_Thread.thread_subject.like('% '+symbol+' %')
	).all()
	like_symbol_ids = [thread.id for thread in like_symbol]

	for count in recent_counts:
		thread_id = count.thread_id
		if thread_id in like_name_ids or thread_id in like_symbol_ids:
			most_recent_thread = thread_query.filter(
				Bitcointalk_Thread.id == thread_id
			).first()
			last_post_time = count.last_post_datetime
			return([most_recent_thread, last_post_time])

# Coin names:
coin_names = ['Bitcoin', 'Litecoin', 'Ethereum', 'NEO', 'Ripple', 'OmiseGO', 'Cardano', 'Verge', 'adToken']
altcoin_names = coin_names[1:] #not bitcoin

# Coin symbols:
coin_symbols = ['BTC', 'LTC', 'ETH', 'NEO', 'XRP', 'OMG', 'ADA', 'XVG', 'ADT']
altcoin_symbols = coin_symbols[1:]

# Coin tuples:
coin_tups = list(zip(coin_names, coin_symbols))
altcoin_tups = coin_tups[1:]

finish_msg = '''
*** Script has finished running. ***
Data was retrieved from:  %s storage.
Coin with largest difference was: %s
Price difference (in BTC): %f
Most recent thread related to the Coin: %s
Time of most recent post: %s
Thread URL: %s
'''

remote_msg = '''
Retrieving live ticker prices and checking for new thread posts from online
data sources.  Ticker prices and new thread posts (if any) will be added to DB.
Live ticker prices will be used to determine largest price difference, and 
new thread posts (along with existing posts in DB) will be included in search 
for most recent relevant thread.
'''

local_msg = '''
Retrieving data from local storage.  The most recent ticker prices stored in DB
will be used to calculate the largest price difference, and the most recent 
relevant thread will be found from posts already stored in DB.
'''

#Create a Session:
Session = sessionmaker(bind=engine)
session = Session()

def main(**kw_source):
	'''
	Takes kwarg as input.
	Check to see if DB exists in current directory, if not, offer to create it.
	If source is remote, pull current data from web and store in DB.
	Retrieve most recent data found in DB (if source is remote, this will be
	the data that was just added).
	Calculate largest price difference across all coins/markets.
	For the coin with largest difference, find most recent thread post related 
	to it in local DB and return URL.
	'''
	# Parse **kw_soiurce:
	source = kw_source['source']
	# Check to see if DB exists and, if not, offer to create it:
	check_db_exists()
	# If specified data source is remote, update DB w/ live data from online sources:
	if source == 'remote':
		print(remote_msg)
		get_live_data_from_web(coin_tups)
	# If specified data source is local, go straight to retrieval:
	elif source == 'local':
		print(local_msg)
	else: 
		print('Invalid data source specified.  Try local or remote.')
		exit()
	# Find coin with the largest price difference:
	[largest_diff, largest_tup] = find_largest_difference(altcoin_tups)
	name, symbol = largest_tup[:2]
	# Find most recent thread:
	[most_recent_thread, last_post_time] = find_most_recent_thread(largest_tup)
	# Collect/prepare output data:
	coin_str = name + ' (' + symbol + ')'
	subject = most_recent_thread.thread_subject
	url = most_recent_thread.thread_url
	
	# Print finishing message:
	msg_args = (source, coin_str, largest_diff, subject, last_post_time, url)
	print(finish_msg % (msg_args))

invalid_source_msg = '''
Invalid data source.
Try: 'local' or 'remote' or key word arg format.
e.g.: python VACCARO_ADAM_hw5.py -source=local
	  python VACCARO_ADAM_hw5.py -source=remote
	  python VACCARO_ADAM_hw5.py source remote
	  etc.

'''

valid_data_sources = ['local', 'remote']

if __name__ == '__main__':
	# Parse command line input into keyword arg, or stop script on bad input:
	num_args = len(sys.argv) #number command line arguments
	error_flag = False #initialize error flag to false
	if num_args == 1:  #Detect misssing source
		print('\nNo datasource specified.')
		error_flag = True
	# Try to parse command line kwarg:
	elif num_args == 2:
		try:
			raw_source = sys.argv[1]
			source = raw_source.strip().lstrip('-')
			pieces = source.split('=')
			k = pieces[0] #== 'source'
			v = pieces[1] #!= ''
		except: error_flag = True
	# Try to parse the 2 positional args into a kwarg:
	elif num_args == 3:
		k = sys.argv[1].strip()
		v = sys.argv[2].strip()
	else: error_flag = True
	# Check if retrieved key, value match kwarg format:
	if not error_flag:
		check1 = k == 'source'
		check2 = v in valid_data_sources
		# If kwarg has been parsed, run script:
		if check1 and check2:
			kw_source = dict()
			kw_source[k] = v
			main(**kw_source)
		else: error_flag = True

	# If unable to parse input (or no input), print error msg and exit:
	if error_flag:
		print(invalid_source_msg)
		exit()