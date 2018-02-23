'''coinmarketcap_api.py
Adam Vaccaro - November 27, 2017
This script collects 24 hour market summary data from the Bittrex.com 
exchange via API.  
'''

# import packages
import json, requests, sys
from datetime import *
# Import necessary SQLAlchemy commands:
import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
# Import SQL table definitions:
from table_definitions import Base, engine
from table_definitions import Coin, Exchange, Market, Bittrex_Ticker

# API Endpoint
api_endpoint = 'https://bittrex.com/api/v1.1/public/getmarketsummary?market=btc-'

#Invalid name error message
invalid_coin_symbol = ''' Error: Invalid coin symbol.
Valid (non-BTC) coin symbols include:
'ltc'
'eth'
'neo'
'''


def check_add_market(market_data, session):
	'''
	Check if market exists in DB.
	Add market to DB if not.
	Retrieve Coin ID to use as foreign key for ticker entry.
	Add market ticker entry to DB.
	'''
	MD = market_data
	market_name = MD['MarketName']
	print('\nChecking if %s exists in DB...\n' % market_name)
	# Check to see if market exists in DB:
	exists_query = session.query(exists().where(Market.market_name == market_name))
	already_exists = exists_query.scalar() #convert to  Boolean
	# If market does not exist, create new Market object and add to DB:
	if already_exists: print('%s already exists in DB.\n' % market_name)
	if not already_exists:
		print('%s does not exist in DB, adding Market.\n' % market_name)
		# Get Bittrex exchange ID to use as foreign key:
		bittrex_query = session.query(Exchange).filter(Exchange.exchange_name == 'Bittrex')
		bittrex_id = [exchange.id for exchange in bittrex_query][0]
		# Retrieve coin IDs to use as foreign keys:
		symbols = market_name.split('-')
		coin_ids = [] #list to store coin ids
		for symbol in symbols:
			coin_query = session.query(Coin).filter(Coin.coin_symbol == symbol) 
			coin_id = [coin.id for coin in coin_query][0]
			coin_ids.append(coin_id)
		# Create new Market object from market data:
		new_market = Market(
			market_name = market_name,
			coin1_id = coin_ids[0],
			coin2_id = coin_ids[1],
			exchange_id = bittrex_id,
			start_date = MD['Created']
		)
		# Add new market to DB
		session.add(new_market)
		session.commit()
	# Retrieve market ID to use as foreignkey:
	for market in session.query(Market).filter(Market.market_name == market_name):
		market_id = market.id
	# New Ticker data entry object:
	new_ticker = Bittrex_Ticker(
		timestamp = MD['TimeStamp'],
		market_id = market_id,
		high24h = MD['High'],
		low24h = MD['Low'],
		volume = MD['Volume'],
		base_volume = MD['BaseVolume'],
		last_price = MD['Last'],
		bid_price =  MD['Bid'],
		ask_price = MD['Ask'],
		open_buy_orders = MD['OpenBuyOrders'],
		open_sell_orders = MD['OpenSellOrders'],
		prev_day = MD['PrevDay']
	)
	# Add ticker entry object to DB:
	session.add(new_ticker)
	session.commit()
	print('%s ticker data added to DB.\n' % market_name)

def access_api(symbol):
	'''Access Bittrex's API w/ (non-BTC) coin symbol as input.'''
	print('\n*** Accessing Bittrex API ***')
	try:
		market_url = api_endpoint + symbol #API endpoint for specific coin market
		market_api = requests.get(market_url) #get request
		market_json = json.loads(market_api.text) #convert to JSON
		market_data = market_json['result'][0] #retrieve coin data dictionary
		# Convert timestamp and create date strings to datetime:
		date_str = market_data['TimeStamp']
		datetime_format = '%Y-%m-%dT%H:%M:%S'
		datetime_ms_format = '%Y-%m-%dT%H:%M:%S.%f'
		market_data['date_str'] = date_str
		time_stamp = datetime.strptime(date_str, datetime_ms_format)
		market_data['TimeStamp'] = time_stamp
		create_str = market_data['Created']
		# match appropriate format to create date string:
		if len(create_str) > 20: create_format = datetime_ms_format
		elif len(create_str) < 20: create_format = datetime_format
		else: print('\n***NO DATETIME FORMAT MATCHED ***')
		start_datetime = datetime.strptime(create_str, create_format)
		market_data['Created'] = start_datetime
		# Create a Session:
		Session = sessionmaker(bind=engine)
		session = Session()
		# Check to see if market is in DB (if not, add market), then add new ticker data:
		check_add_market(market_data, session)
		return(market_data)
	except:
		print(invalid_coin_symbol)

def debug_message(market_data, symbol):
	MD = market_data
	header = '\n*** Outputing Bittrex market data for ' + MD['MarketName'] + '*** \n'
	description = '''

This data source is the 24 hour market summary of %s exchanges from bittrex.com.  
We are retrieving all available market data, including: High and low prices, 
24 hour volume, current Bid and Ask prices,and a time stamp.  Sample output 
includes the 24 hour high and low, the current bid and ask prices, and a time 
stamp from when the data was retrieved. \n\n''' % MD['MarketName']

	URL_str = 'URL: ' + api_endpoint + symbol + '\n'
	output_header = '\nSample output:\n'
	market_str = 'Market: ' + MD['MarketName'] + '\n'
	high_str = '24h high: ' + str(MD['High']) + '\n'
	low_str = '24h low: ' + str(MD['Low']) + '\n'
	bid_str = 'Current bid price: ' + str(MD['Bid']) + '\n'
	ask_str = 'Current ask price: ' + str(MD['Ask']) + '\n'
	time_str = 'Time stamp: ' + MD['date_str'] + '\n'
	output = header + description + URL_str + output_header + market_str + high_str + low_str + bid_str + ask_str + time_str
	print(output)


def main(symbol):
	MD = access_api(symbol) 
	debug_message(MD, symbol)
	

if __name__ == "__main__":
	if len(sys.argv) > 1:
		symbol = sys.argv[1]
	elif len(sys.argv) == 1:
		print('Error: need input.\n')
		exit()
	main(symbol)