'''bitcointalk_scraper.py
Adam Vaccaro - November 27, 2017
This script scrapes data from the bitcointalk.com forum's
Speculation (Altcoins) board.
'''

# import packages:
import requests, sys, warnings
from bs4 import BeautifulSoup
import datetime
from datetime import datetime
# Import necessary SQL alchemy commands:
import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
# Import SQL table definitions:
from table_definitions import Base, engine
from table_definitions import Bitcointalk_Thread, Bitcointalk_Count

# Bitcointalk Speculation (Altcoins) URL:
SPEC_ALT_URL = 'https://bitcointalk.org/index.php?board=224.0'

def extract_tr_data(tr,web_date):
	'''
	Function to extract data from table rows and store it in
	SQLAlchemy table objects as defined in table_definitions.py
	'''
	temp = {} #temporary dictionary to store thread data
	#Extract data from table rows:
	row_data = tr.find_all('td')
	table_datas = [td for td in row_data]
	thread_link = table_datas[2].find_all('a')[0]
	thread_url = thread_link.get('href') #URL to thread
	thread_subject = thread_link.text #Thread Subject (title)
	thread_author_link = table_datas[3].find_all('a')[0]
	thread_author = thread_author_link.text #Author's name
	thread_author_url = thread_author_link.get('href') #URL to author's page
	thread_replies = table_datas[4].text.strip() #number of replies
	thread_views = table_datas[5].text.strip() #number of views
	thread_last_post = str(table_datas[6].find_all('span'))
	datetime_format = '%B %d, %Y, %I:%M:%S %p' #format used on website
	if 'Today' in thread_last_post: 
	# If thread is from today, replace 'Today' with date string:
		last_post_time = thread_last_post.split('at ')[1].split('<br/>')[0]
		last_post_datestr = web_date + ', ' + last_post_time
		last_post_datetime = datetime.strptime(last_post_datestr, datetime_format)
	else:
		last_post_datestr = thread_last_post.split('>')[1].split('<')[0].strip()
		try:
			last_post_datetime = datetime.strptime(last_post_datestr, datetime_format)
		except Exception as e:
			print(e)
			print(last_post_datestr)
	# Add data to temp dictionary:
	temp['subject'] = thread_subject
	temp['author'] = thread_author
	temp['url'] = thread_url
	temp['author url'] = thread_author_url
	temp['replies'] = thread_replies
	temp['views'] = thread_views
	temp['last'] = last_post_datetime
	return(temp)

def scrape_page(url):
	'''
	Function to scrape a given url.
	First, get request and convert to soup.
	Extract date according to website.
	Find table rows in main table (excluding header row).
	'''
	r = requests.get(url) #get request
	soup = BeautifulSoup(r.text, 'lxml') #convert to soup
	# Get date according to website:
	web_datestr =  str(soup.find_all(
		'span', {'class' : 'smalltext'})[0]).split('>')[1].split('<'
	)[0]
	#web_datetime = datetime.strptime(web_datestr, '%B %d, %Y, %I:%M:%S %p')
	pieces = web_datestr.split(',')
	web_date = pieces[0] + ',' + pieces[1]
	# Find data in main table:
	main_table = soup.find_all('div', {'class' : 'tborder'})[1].find_all('tr')
	table_rows = [tr for tr in main_table]
	table_rows = table_rows[1:] #skip headers
	return([table_rows, web_date, soup])

def get_next_url(soup, current_url):
	'''
	Function to get next url (if possible).
	Get numerical suffix from current url.
	Get numerical suffixes from navigation buttons.
	Check for navigation suffix greater than current.
	'''
	# Extract numerical suffix from current url:
	current_num = current_url.split('=')[1]
	current_suf = int(current_num.split('.')[1])
	# Check against numerical suffixes from navigation buttons:
	nav_buttons = soup.find_all('span', {'class' : 'prevnext'})
	for button in nav_buttons:
		nav_url = button.find_all('a')[0].get('href')
		nav_num = nav_url.split('=')[1]
		nav_suf = int(nav_num.split('.')[1])
		if nav_suf > current_suf: return(nav_url)
	return(None) 



def check_add_thread_count(temp, current_update_time, session):
	'''
	Function to check if thread exists in DB.
	If it does, create timestamp data object.
	If it does not, create a metadata table object and timestamp data object.
	'''
	# Initialize flag (binary) to see if thread exists to 0:
	thread_added = 0
	# Check to see if thread exists in DB:
	already_exists = session.query(exists().where(
		Bitcointalk_Thread.thread_url == temp['url'])
	).scalar()
	# If thread does not exist, create a new Thread object and add to DB:
	if not already_exists:
		new_thread = Bitcointalk_Thread(
			thread_subject = temp['subject'],
			thread_author = temp['author'],
			thread_url = temp['url']
		)
		session.add(new_thread)
		session.commit()
		thread_added = 1
	# Retrieve thread ID to use as foreign key:
	for thread in session.query(Bitcointalk_Thread).filter(
		Bitcointalk_Thread.thread_url == temp['url']
	): 
		bit_thread_id = thread.id
	# Create new Count object and add to DB:
	new_count = Bitcointalk_Count(
		thread_views = temp['views'],
		thread_replies = temp['replies'],
		last_post_datetime = temp['last'],
		update_datetime = current_update_time,
		thread_id = bit_thread_id
	) 
	session.add(new_count)
	session.commit()
	return(thread_added)
def scrape_threads(end_time='last', echo=False):
	'''
	Function to scrape threads until a specified end time and store data in SQL database.
	First parse end_time argument and set appropriate end_datetime.
	Then scrape through threads until finding a thread with last post time older than end_datetime.
	'''	

	print('\n*** Starting Bitcointalk webscraper. ***')
	# Create a Session:
	Session = sessionmaker(bind=engine)
	session = Session()
	# Get current time as datetime:
	current_datetime = datetime.now()
	# Parse end_time argument:
	if end_time == 'end':
		print('\n*** Scraping entire board, this may take a few minutes... ***')
		# Set end time to datetime that pre-dates the creation of the board
		end_datetime = datetime.strptime('2010-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
	elif end_time == 'last':
		try:
			# Set end time to datetime from last update
			query = session.query(Bitcointalk_Count)
			last_entry = query.order_by(Bitcointalk_Count.last_post_datetime.desc()).first()
			end_datetime = last_entry.last_post_datetime
			print('\n*** Scraping until last post recorded in DB. ***')
			print('\nLast post time in DB: %s' % end_datetime)
			#print(end_datetime)
		except Exception as e:
			print(e)
			print('Could not find last post time.\n' + 
				'Initialize DB to populate table with entries.\n'
			)
			exit()
	elif type(end_time) is datetime.datetime:
		end_datetime = end_time
	else:
		invalid_end_msg = ['\nError: invalid end time\n' + 
		'Try: (null), last, or a datetime object\n']
		print(invalid_end_msg[0])
		exit()

	start_datetime = datetime.now()
	threads_dict = {} #initialize empty dictionary to store thread data in (for debug msg)
	new_post_datetime = datetime.strptime('3000','%Y')  #initialize new post time in the future
	current_url = SPEC_ALT_URL #initialize current url as front page
	print('\nStarting at URL: %s' % current_url)
	print('Start time: %s \n' % start_datetime)
	# Initialize counters for number of new threads/counts added at 0:
	N_new_threads = 0 
	N_counts_added = 0
	# Condition for while loop:
	flag = new_post_datetime > end_datetime 
	while flag:
		if echo: #Output current URL as scraping progresses
			print('\nCurrent url:')
			print(current_url)
		# Scrape page to retrieve table rows, date according to website, and soup:
		[table_rows, web_date, soup] = scrape_page(current_url)
		for tr in table_rows: 
			if tr.find_all('img', {'id' : 'stickyicon15783712'}): continue #skip stickied posts
			temp = extract_tr_data(tr, web_date) #extract tr data to temporary dictionary
			new_post_datetime = temp['last']
			# If new post datetime is less recent than specified end datetime, set flag to False:
			if new_post_datetime <= end_datetime: flag = False
			# If flag still True, add current data to DB:
			if flag: 
				added = check_add_thread_count(temp, current_datetime, session)
				N_new_threads = N_new_threads + added
				N_counts_added += 1
			# If flag is False, break for loop:
			elif flag is False: 
				print('\n*** Finished scraping until endtime or last thread. ***\n')
				break 
		# If flag still True after exhausting threads on current page, try to go to next page:
		if flag is True:
			next_url = get_next_url(soup, current_url)
			if next_url is not None: 
				current_url = next_url
			elif next_url is None: #only if finished scraping entire website
				print('\n*** Finished scraping all threads. ***\n')
				break
	# Print information about webscraping:
	finish_datetime = datetime.now()
	print('\nFinished at URL: %s' % current_url)
	print('Finish time: %s' % finish_datetime)
	print('\nNew post time: %s' % new_post_datetime)
	print('End post date time: %s' % end_datetime)
	print('\nNumber of new threads added: %i' % int(N_new_threads))
	print('Number of thread view/reply counts added: %i\n' % int(N_counts_added))
	return(temp)


def debug_message(temp):
	header = '\n*** Outputing forum data from Bitcointalk.com ***\n'
	description = '''

This data source is the Speculation (Altcoins) board on bitcointalk.
The webscraper collects meta data and a URL for each thread and creates 
a dictionary for each thread.  It then checks to see if the thread exists
in the SQL DB and, if not, adds thread data to DB. Also adds count data
for all threads with last post more recent than specified end search time.
Sample output is the dictionary created from the most recent thread on 
the board.

'''
	URL_str = 'URL: ' + SPEC_ALT_URL + '\n'
	output_header = '\nSample output:\n'
	output = header + description + URL_str + output_header
	print(output)
	print(temp)

# ignore annoying SQLalchemy warning:
warnings.filterwarnings('ignore')



def main(end_time):
	try:
		temp = scrape_threads(end_time)
		debug_message(temp)
	except Exception as e:
		print(e)

if __name__ == "__main__":
	end_time = 'last'
	if len(sys.argv) > 1: end_time = sys.argv[1]
	main(end_time)