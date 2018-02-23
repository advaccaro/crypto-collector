''' VACCARO_ADAM_hw4.py
Adam Vaccaro
INF510 - Dr. Jeremy Abramson
USC - Fall 2017

Purpose: Access all three data sources with ability to specify which 
source (and additional configuration parameters) via command line.

Outputs: Brief debugging message describing what the data source is,
where it is retrieved from, and exactly what is being retrieved.
Also, preview of a few items from data source.


Input syntax:
Valid data sources = 'bitcointalk', 'bittrex', 'coinmarketcap'

bitcointalk requires no additional parameters.
Sample syntax: python VACCARO_ADAM_hw4.py bitcointalk



bittrex takes one parameter: coin symbol (that is not bitcoin/BTC).
Valid symbols include: 'ltc', 'eth', 'neo', etc.
Sample syntax: python VACCARO_ADAM_hw4.py bittrex ltc
			   python VACCARO_ADAM_hw4.py bittrex eth



coinmarketcap takes one parameter: coin name
Valid coin names include: 'bitcoin', 'litecoin', 'ethereum', 'neo', etc.
Sample syntax: python VACCARO_ADAM_hw4.py coinmarketcap bitcoin
			   python VACCARO_ADAM_hw4.py coinmarketcap neo

'''

# import modules and libraries
import sys


#Prepare error messages:
valid_sources = ['bitcointalk', 'bittrex', 'coinmarketcap']
valid_sources_msg = '''
Valid data source names are: \n%s\n%s\n%s
''' % (valid_sources[0], valid_sources[1], valid_sources[2])

no_source_msg = '\nError: No data source specified.\n'+valid_sources_msg

invalid_source_msg = '\nError: Invalid data source.\n'+valid_sources_msg

additional_parameters_msg = '''
Error: bittrex and coinmarketcap data sources require
an additional parameter beyond the data source.
'''

# define main functionality:
def main(data_source,data_parameters):
	#Check for valid data source:
	if data_source not in valid_sources:
		print(invalid_source_msg)
		exit()

	#If data source is bitcointalk, try to run bitcointalk webscraper:
	if data_source == 'bitcointalk':
		try:
			import bitcointalk_scraper
			bitcointalk_scraper.scrape_threads()
		except Exception as e:
			print(e)
	#If the data source is not bitcointalk, check for additional inputs:
	elif len(data_parameters) < 1:
		print(additional_parameters_msg)
		exit()

	#If data source is bittrex, try to run bittrex API accessor:
	elif data_source == 'bittrex':
		try:
			import bittrex_api
			symbol = data_parameters[0]
			bittrex_api.access_api(symbol)
		except Exception as e:
			print(e)

	#If data source is coinmarketcap, try to run coinmarketcap API accessor:
	elif data_source == 'coinmarketcap':
		try:
			import coinmarketcap_api
			coin = data_parameters[0]
			coinmarketcap_api.access_api(coin)
		except Exception as e:
			print(e)


# enable command-line functionality:
if __name__ == '__main__':
	#Check for input data source:
	if len(sys.argv) == 1:
		print(no_source_msg)
		exit()
	data_source = sys.argv[1]
	data_parameters = [] #initialize empty list to hold variable number of inputs (if necessary)
	for ii in range(2,len(sys.argv)):
		data_parameters.append(sys.argv[ii])
	main(data_source, data_parameters)