'''
INF 510 - Homework 5
Adam Vaccaro
Purpose: Define classes for storing data in SQL database
'''

#import SQL Alchemy
from sqlalchemy import *
#from sqlalchemy import create_engine, ForeignKey
#from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import os


# Project directory: (move this elsewhere)
project_root = os.path.dirname(os.path.abspath(__file__))

#engine = create_engine('sqlite:////Users/ADV/Documents/INF510/Final/crypto.db', echo=False)
DB_FILE_NAME = 'crypto.db'
ABS_DB_PATH = project_root + '/' + DB_FILE_NAME
sqlite_engine_str = 'sqlite:///' + ABS_DB_PATH
engine = create_engine(sqlite_engine_str, echo=False)
Base = declarative_base()

class Exchange(Base):
	'''Table for different exchanges'''
	__tablename__ = 'exchanges'
	# Table columns:
	id = Column(Integer, primary_key=True)
	exchange_name = Column(String)
	exchange_url = Column(String, unique=True)

class Coin(Base):
	'''Table for different coins'''
	__tablename__ = 'coins'
	# Table columns:
	id = Column(Integer, primary_key=True)
	coin_name = Column(String, unique=True)
	coin_symbol = Column(String, unique=True)

class Market(Base):
	'''Table for different markets'''
	__tablename__ = 'markets'
	# Table columns:
	id = Column(Integer, primary_key=True)
	market_name = Column(String)
	coin1_id = Column(Integer, ForeignKey('coins.id'))
	coin2_id = Column(Integer, ForeignKey('coins.id'))
	exchange_id = Column(Integer, ForeignKey('exchanges.id'))
	start_date = Column(DateTime)
	# Table relationships:
	coin1 = relationship('Coin', foreign_keys=[coin1_id])
	coin2 = relationship('Coin', foreign_keys=[coin2_id])
	coin_exchange = relationship('Exchange')
	# Table index:
	Index('market_ind', 'coin1_id', 'coin2_id', 'exchange_id', unique=True)

class Bittrex_Ticker(Base):
	'''Table for market data pulled from bittrex'''
	__tablename__ = 'bittrex_ticker_entries'
	# Table columns:
	id = Column(Integer, primary_key=True)
	timestamp = Column(DateTime)
	market_id = Column(Integer, ForeignKey('markets.id'))
	high24h = Column(Float)
	low24h = Column(Float)
	volume = Column(Float)
	base_volume = Column(Float)
	last_price = Column(Float)
	bid_price = Column(Float) 
	ask_price = Column(Float)
	open_buy_orders = Column(Integer)
	open_sell_orders = Column(Integer)
	prev_day = Column(Float)
	# Table relationships:
	coin_market = relationship('Market')

class Coinmarketcap_Ticker(Base):
	'''Table for coin pricing data pulled from coinmarketcap.com'''
	__tablename__ = 'coinmarketcap_ticker_entries'
	# Table columns:
	id = Column(Integer, primary_key=True)
	coin_id = Column(Integer, ForeignKey('coins.id'))
	price_usd = Column(Float)
	price_btc = Column(Float)
	volume_24h_usd = Column(Numeric)
	market_cap_usd = Column(Numeric)
	available_supply = Column(Numeric)
	total_supply = Column(Numeric)
	max_supply = Column(Numeric)
	percent_change_1h = Column(Float)
	percent_change_24h = Column(Float)
	percent_change_7d = Column(Float)
	rank = Column(Integer)
	last_updated = Column(DateTime)
	# Table relationships:
	coin1 = relationship('Coin')

class Bitcointalk_Thread(Base):
	'''Table for thread meta data from bitcointalk.com'''
	__tablename__ = 'bitcointalk_threads'
	# Table columns:
	id = Column(Integer, primary_key=True)
	thread_subject = Column(String)
	thread_author = Column(String)
	thread_url = Column(String, unique=True)

class Bitcointalk_Count(Base):
	'''Table for thread reply/view counts from bitcointalk.com'''
	__tablename__ = 'bitcointalk_counts'
	# Table columns:
	id = Column(Integer, primary_key=True)
	thread_views = Column(Integer)
	thread_replies = Column(Integer)
	last_post_datetime = Column(DateTime)
	update_datetime = Column(DateTime)
	thread_id = Column(Integer, ForeignKey('bitcointalk_threads.id'))
	# Table relationships:
	thread = relationship('Bitcointalk_Thread')