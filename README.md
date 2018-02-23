Adam Vaccaro
INF 510 - Homework 6

README file for entire project.

1. USAGE NOTES

VACCARO_ADAM_hw5.py is the master script; it accesses all supporting libraries
and modules as necessary.  When the script is run, it will first check to see
if the SQLite database exists, and if not, the script will offer to create it.
Once a connection has been made to the database, the script will then retrieve
data (from local or remote source), add new data to database (if pulling from
the remote sources), and then return the coin with the largest price difference
between the two pricing data sources.  

The only parameter for VACCARO_ADAM_hw5.py is the data source, which can be 
local or remote.

Sample syntax from command-line:
VACCARO_ADAM_hw5.py -source=remote
VACCARO_ADAM_hw5.py -source=local

The script is also prepared to parse similar formats (--source='local', 
source local, etc.), but it's probably best to just use -source=local/remote.



2. ISSUES/AREAS FOR IMPROVEMENT

In order to create high resolution timestamped data on a common time axis, this
script should be automated to run at uniform time steps.  Ideally it would run
frequentyly (say, once an hour, or even better, once every minute) and make
regular updates to the database.  To this end, the database and supporting code
should be placed on a webserver so it can make automatic pulls from the web
sources (using crontab/cron job) while having enough storage space for the
database as it continues to grow.

Another issue is that the scripts are currently not integrating the text 
contained within the Bitcointalk forum posts, only the thread subject (title).
Analyzing the forum post text would undoubtedly augment the quality and
quantity of information we could extract from the forums.  It would be nice to
run some sort of NLP analysis on the text, but this is beyond my level of
understanding at the moment.


3. OTHER RELEVANT NOTES

The script assumes that the SQLite database is in the current working
directory.  If the DB is elsewhere, the script won't find it and will instead
create an entirely new DB with the same name in the current working directory.

Also, I included the SQLite DB (crypto.db) in the zip file, but if you want to
see how the script performs when the database is not found, just rename, move,
or delete the existing DB and run the master script again.# crypto-collector
