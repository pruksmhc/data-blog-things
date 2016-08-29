import os
import sys
import csv
import pycountry
import sqlite3
from collections import Counter
import place
from extraction import Extractor
import nltk
from nltk import word_tokenize,sent_tokenize
import httplib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
import urllib2

# Extracting the html links from TechCrunch

def get_data(category,):

    opener = urllib2.build_opener()
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    opener.addHeaders = headers.items()
    url = 'https://techcrunch.com/tag/' + category + '/'
    response = opener.open(url)
    page_number = 1
    while True:
        html = response.read()

        links = set()
        for link in BeautifulSoup(html, parseOnlyThese=SoupStrainer('a', href=True)):
            # This removes all links that look like "#", '/', '/europe', and so on.
            if ('techcrunch.com/2' in link['href']):
                links.add(link['href'])

        f = open("./data/output", "w")
        links = ',\n'.join(links)
        f.write(links[:-1])
        f.close()
        if 'page' in url:
            url.split('page')[0]
            url = url + 'page/' + page_number
        else: 
            url = url + 'page/2/'
        page_number  = page_number + 1
        try:
            response = opener.open(url)
        except Exception as e: 
            break

# Getting the countries from the text
def get_place_context(url, dirname, text=None):

    f = open(dirname + 'blog-3/geograpy2/data/output_new', "w"); 
    f.write('')
    f.close()
    e = Extractor(url=url, text=text)
    e.find_entities()
    pc = PlaceContext(e.places) 
    pc.set_countries()
    output_str = ""
    countries = pc.countries
    country_str = ','.join([i for i in pc.countries])
    f = open(dirname +'blog-3/geograpy2-modified/data/output_new', 'a'); 
    f.write(country_str)
    f.close()
    return pc


class PlaceContext(object):

    """
    Attributes:
      places (list of place): The list of possible place names found. 
      names (list of unicode): The list of possible place names found.
      conn (object):
       
    Raises:
        IOError: if cannot write to DB

    """

    def __init__(self, place_names, db_file=None):   
        nltk.downloader.download('words')
        nltk.downloader.download('treebank')
        nltk.downloader.download('maxent_treebank_pos_tagger  ')
        db_file = db_file or os.path.dirname(os.path.realpath(__file__)) + "/locs.db"
        open(db_file, 'w') # just checks if writing is allowed

        self.conn = sqlite3.connect(db_file)
        self.conn.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
        self.names = place_names
        self.places = []

    def populate_db(self):
        cur = self.conn.cursor()
        cur.execute("DROP TABLE IF EXISTS cities")

        cur.execute("CREATE TABLE cities(geoname_id INTEGER, continent_code TEXT, continent_name TEXT, country_iso_code TEXT, country_name TEXT, subdivision_iso_code TEXT, subdivision_name TEXT, city_name TEXT, metro_code TEXT, time_zone TEXT)")
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        with open(cur_dir+"/data/GeoLite2-City-Locations.csv", "rb") as info:
            reader = csv.reader(info)
            for row in reader:
                cur.execute("INSERT INTO cities VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", row)
            self.conn.commit()


    def db_has_data(self):
        cur = self.conn.cursor()

        cur.execute("SELECT Count(*) FROM sqlite_master WHERE name='cities';")
        data = cur.fetchone()[0]

        if data > 0:
            cur.execute("SELECT Count(*) FROM cities")
            data = cur.fetchone()[0]
            return data > 0

        return False


    def correct_country_mispelling(self, s):
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        with open(cur_dir+"/data/ISO3166ErrorDictionary.csv", "rb") as info:
            reader = csv.reader(info)
            for row in reader:
                if s in remove_non_ascii(row[0]):
                    return row[2]
        return s

    
    def is_a_country(self, s): 
        s = self.correct_country_mispelling(s)
        try:
            pycountry.countries.get(name=s)
            return True
        except KeyError, e:
            if s in ["Korea", "South Korea", "North Korea"]:
                return True
            return False

    
    
    def places_by_name(self, place_name, column_name):
        if not self.db_has_data():
            self.populate_db()

        cur = self.conn.cursor()
        cur.execute('SELECT * FROM cities WHERE ' + column_name + ' = "' + place_name + '"')
        rows = cur.fetchall()

        if len(rows) > 0:
            return rows

        return None


    def set_countries(self):
        countries = [self.correct_country_mispelling(place) 
            for place in self.names if self.is_a_country(place)]

        self.country_mentions = Counter(countries).most_common()
        self.countries = list(countries)



if __name__ == "__main__":
    category = sys.argv[1]
    dirname = sys.argv[2]
    get_data(cateogry)
    with open("./data/output", "r") as file:
        for url in csv.reader(file):
            get_place_context(url[0], dirname)
    with open("./data/output_new", "r") as file:
        table = {}
        for line in csv.reader(file):
            for place in line:
                if place in table.keys():
                    table[place] = table[place] + 1
                else: 
                    table[place] = 1
    with open('./data/output_final.csv', 'w') as f:
            w = csv.DictWriter(f, table.keys())
            w.writeheader()
            w.writerow(table)




