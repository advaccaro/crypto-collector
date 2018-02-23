'''coinmarketcap_api.py
Adam Vaccaro - November 27, 2017
This script collects the latest ticker data for a specified cyrptocurrency
from coinmarketcap.com via API.
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
from table_definitions import Coin, Coinmarketcap_Ticker


# API Endpoint
api_endpoint = 'https://api.coinmarketcap.com/v1/ticker/'


#Invalid name error message
invalid_coin_name = ''' Error: Invalid coin name.
Valid coin names include:
'bitcoin'
'litecoin'
'ethereum'
'neo'
'''

def check_add_coin(coin_data, session):
	'''
	Check if coin exists in DB. 
	Add coin to DB if not.
	Retrieves Coin ID to use as foreignkey for ticker data entry.
	Add coin ticker data entry to DB
	'''
	CD = coin_data
	print('\nChecking if %s exists in DB...\n' % CD['name'])
	# Check to see if coin exists in DB:
	already_exists = session.query(
		exists().where(Coin.coin_name == CD['name'])
	).scalar()
	if already_exists: print('%s already exists in DB.\n' % CD['name'])
	# If coin does not exist, create new Coin object and add to DB:
	if not already_exists:
		print('%s does not exist in DB, adding Coin.\n' % CD['name'])
		# Create new Coin object from coin data:
		new_coin = Coin(
		coin_name = CD['name'],
		coin_symbol = CD['symbol']
		)
		# Add new coin to DB:
		session.add(new_coin)
		session.commit()
		print('%s added to DB.' % CD['name'])
	# Retrieve coin ID to use as ticker foreign key:
	for coin in session.query(Coin).filter(Coin.coin_name == CD['name']): 
		fid = coin.id
	# Create new Ticker data entry object:
	new_ticker = Coinmarketcap_Ticker(
		coin_id = fid,
		price_usd = CD['price_usd'],
		price_btc = CD['price_btc'],
		volume_24h_usd = CD['24h_volume_usd'],
		market_cap_usd = CD['market_cap_usd'],
		available_supply = CD['available_supply'],
		total_supply = CD['total_supply'],
		max_supply = CD['max_supply'],
		percent_change_1h = CD['percent_change_1h'],
		percent_change_24h = CD['percent_change_24h'],
		percent_change_7d = CD['percent_change_7d'],
		rank = CD['rank'],
		last_updated = CD['last_updated']
	)
	# Add ticker data entry object to DB:
	session.add(new_ticker)
	session.commit()
	print('%s ticker data added.\n' % CD['name'])

def access_api(coin):
	'''Access coinmarketcap's API w/ coin name as input'''
	print('\n*** Accessing CoinMarketCap API ***')
	try:
		coin_url = api_endpoint + coin #API endpoint for specific coin
		coin_api = requests.get(coin_url) #get request
		coin_json = json.loads(coin_api.text) #convert to JSON
		coin_data = coin_json[0] #retrieve coin data dictionary
		# Convert datestr to datetime:
		date_str = datetime.fromtimestamp(
			int(coin_data['last_updated'])
		).strftime('%Y-%m-%d %H:%M:%S')
		coin_data['date_str'] = date_str
		last_datetime = datetime.strptime(date_str,'%Y-%m-%d %H:%M:%S')
		coin_data['last_updated'] = last_datetime
		# Create a Session:
		Session = sessionmaker(bind=engine)
		session = Session()
		# Check to see if coin is in DB (if not, add coin), then add new ticker data:
		check_add_coin(coin_data, session)
		return(coin_data)
	except:
		print(invalid_coin_name)

def debug_message(coin_data, coin):
	'''Prepare and print debug message.'''
	CD = coin_data
	name_str = CD['name'] + ' (' + CD['symbol'] +')\n'
	header = '\n*** Outputing coinmarketcap data for '+ name_str + '*** \n'
	description = '''

This data source is the latest ticker data for %s from coinmarketcap.com.  
We are retrieving all of the ticker data, including: price in USD, price in BTC, 
24h volume in USD, market capacity in USD, percent change over the last hour, 
percent change over the last 24 hours, and percent change over the last 7 days.  
Sample output includes the price in USD and BTC, percent change over the last 
24 hours, and time of last update.

''' % name_str
	URL_str = 'URL: ' + api_endpoint + coin + '\n'
	output_header = '\nSample output:\n'
	price_str = 'Price in USD: ' + CD['price_usd'] +'\nPrice in BTC: ' + CD['price_btc'] + '\n'
	percent_str = 'Percent change over past 24 hours: ' + CD['percent_change_24h'] +'\n'
	date_str = CD['date_str']
	update_str = 'Time of last update: ' + date_str +'\n'
	output = header + description + URL_str + output_header + name_str + price_str + percent_str + update_str
	print(output)


def main(coin):
	try:
		CD = access_api(coin)
		debug_message(CD, coin)
	except Exception as e:
		print(e)

	

if __name__ == "__main__":
	coin = sys.argv[1]
	main(coin)