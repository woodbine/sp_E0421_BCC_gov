# -*- coding: utf-8 -*-

#### IMPORTS 1.0

import os
import re
import scraperwiki
import urllib2
from datetime import datetime
from bs4 import BeautifulSoup


#### FUNCTIONS 1.2
import requests    #import requests library to validate url


def validateFilename(filename):
    filenameregex = '^[a-zA-Z0-9]+_[a-zA-Z0-9]+_[a-zA-Z0-9]+_[0-9][0-9][0-9][0-9]_[0-9QY][0-9]$'
    dateregex = '[0-9][0-9][0-9][0-9]_[0-9QY][0-9]'
    validName = (re.search(filenameregex, filename) != None)
    found = re.search(dateregex, filename)
    if not found:
        return False
    date = found.group(0)
    now = datetime.now()
    year, month = date[:4], date[5:7]
    validYear = (2000 <= int(year) <= now.year)
    if 'Q' in date:
        validMonth = (month in ['Q0', 'Q1', 'Q2', 'Q3', 'Q4'])
    elif 'Y' in date:
        validMonth = (month in ['Y1'])
    else:
        try:
            validMonth = datetime.strptime(date, "%Y_%m") < now
        except:
            return False
    if all([validName, validYear, validMonth]):
        return True


def validateURL(url):
    try:

        r = requests.get(url)
        count = 1
        while r.status_code == 500 and count < 4:
            print ("Attempt {0} - Status code: {1}. Retrying.".format(count, r.status_code))
            count += 1
            r = requests.get(url)
        sourceFilename = r.headers.get('Content-Disposition')
        if sourceFilename:
            ext = os.path.splitext(sourceFilename)[1].replace('"', '').replace(';', '').replace(' ', '')
        else:
            ext = os.path.splitext(url)[1]
        validURL = r.status_code == 200
        validFiletype = ext.lower() in ['.csv', '.xls', '.xlsx', '.pdf']
        return validURL, validFiletype
    except:
        print ("Error validating URL.")
        return False, False


def validate(filename, file_url):
    validFilename = validateFilename(filename)
    validURL, validFiletype = validateURL(file_url)
    if not validFilename:
        print filename, "*Error: Invalid filename*"
        print file_url
        return False
    if not validURL:
        print filename, "*Error: Invalid URL*"
        print file_url
        return False
    if not validFiletype:
        print filename, "*Error: Invalid filetype*"
        print file_url
        return False
    return True


def convert_mth_strings ( mth_string ):
    month_numbers = {'JAN': '01', 'FEB': '02', 'MAR':'03', 'APR':'04', 'MAY':'05', 'JUN':'06', 'JUL':'07', 'AUG':'08', 'SEP':'09','OCT':'10','NOV':'11','DEC':'12' }
    for k, v in month_numbers.items():
        mth_string = mth_string.replace(k, v)
    return mth_string

#### VARIABLES 1.0

entity_id = "E0421_BCC_gov"
url = "http://www.buckscc.gov.uk/services/council-and-democracy/open-data/spending-over-500/"
archive_url = 'https://data.gov.uk/dataset/payments-to-suppliers-over-500-from-buckinghamshire-county-council-2012-2013'
errors = 0
data = []

#### READ HTML 1.0

html = urllib2.urlopen(url)
soup = BeautifulSoup(html, 'lxml')


#### SCRAPE DATA
import urlparse
import urllib
from datetime import datetime

block = soup.find('div',{'class':'related-media'})
links = block.findAll('a', href=True)
for link in links:
    url = 'http://www.buckscc.gov.uk' + link['href']
    parsed_link = urlparse.urlsplit(url.encode('utf8'))
    parsed_link = parsed_link._replace(path=urllib.quote(parsed_link.path))
    encoded_link = parsed_link.geturl()
    if '.csv' in encoded_link:
        title = link.contents[0]
        csvYr = title.split(' ')[1]
        csvMth = title.split(' ')[0][:3]
        csvMth = convert_mth_strings(csvMth.upper())
        data.append([csvYr, csvMth, encoded_link])
archive_html = urllib2.urlopen(archive_url)
archive_soup = BeautifulSoup(archive_html, 'lxml')
rows = archive_soup.find_all('div', 'dataset-resource')
for row in rows:
    title = row.find('span', 'inner-cell').text.strip().split(' ')
    # title = row.find('div', 'inner2').text.strip().split(' ')
    year = title[-1]
    month = title[-2]
    doc_date = year+' '+month
    if '20' in doc_date:
        csv_date = datetime.strptime(doc_date, "%Y %B")
        march_date = datetime.strptime('2014 March', "%Y %B")
        if csv_date < march_date:
            csvYr = year
            csvMth = month[:3]
            url = row.find('a', 'js-tooltip')['href']
            parsed_link = urlparse.urlsplit(url.encode('utf8'))
            parsed_link = parsed_link._replace(path=urllib.quote(parsed_link.path))
            encoded_link = parsed_link.geturl()
            csvMth = convert_mth_strings(csvMth.upper())
            data.append([csvYr, csvMth, encoded_link])

#### STORE DATA 1.0

for row in data:
    csvYr, csvMth, url = row
    filename = entity_id + "_" + csvYr + "_" + csvMth
    todays_date = str(datetime.now())
    file_url = url.strip()

    valid = validate(filename, file_url)

    if valid == True:
        scraperwiki.sqlite.save(unique_keys=['l'], data={"l": file_url, "f": filename, "d": todays_date })
        print filename
    else:
        errors += 1

if errors > 0:
    raise Exception("%d errors occurred during scrape." % errors)


#### EOF
