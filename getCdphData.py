#!/usr/bin/env python3

import os
import re
import urllib
import datetime
import unicodedata
import pickle

import requests
from bs4 import BeautifulSoup
import numpy as np

class CdphCovidData(object):
    def __init__(self):
        self.baseUrl = 'https://www.cdph.ca.gov'
        self.newsReleaseUrl = urllib.parse.urljoin(self.baseUrl, '/Programs/OPA/Pages/New-Release-2020.aspx')
        self.data = {}

    def getData(self, force=False):
        response = requests.get(self.newsReleaseUrl)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get news releases - look for links with the string 'Latest COVID-19 Facts'
        links = soup.find_all('a')
        for link in links:
            if link.findChild(string=re.compile('Latest COVID-19 Facts')) is None:
                continue
            url = link.get('href')

            # Convert to an absolute url
            if not url.startswith('http'):
                url = urllib.parse.urljoin(self.baseUrl, url)

            # Load the news release
            if url in self.data and not force:
                print(f'\n{url} - already parsed, skipping')
                self.printRecord(self.data[url])
            else:
                print(f'\n{url}')
                self.parseNewsRelease(url)

    def parseNewsRelease(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for match in soup.find_all('span'):
            match.unwrap()    
        
        dateStrings = soup.find_all(string=re.compile('Date:'))
        assert len(dateStrings) == 1, 'Expect to find exactly one date string!'
        dateString = unicodedata.normalize('NFKD', dateStrings[0])
        dateString = dateStrings[0].split(':')[1].strip()
        releaseDate = datetime.datetime.strptime(dateString, '%B %d, %Y')
        print(releaseDate)

        releaseStrings = soup.find_all(string=re.compile('Number:'))
        assert len(releaseStrings) == 1, 'Expect to find exactly one release string!'
        releaseString = unicodedata.normalize('NFKD', releaseStrings[0])
        release = releaseString.split(':')[1].strip()

        record = {'releaseDate': releaseDate, 'releaseNumber': release, 'cases': None, 'deaths': None, 'testsConducted': None, 'testsReceived': None, 'testsPending': None, 'webResponse': response}
        
        # Look for cases and deaths in confirmed cases string (first paragraph)
        strings = self.findString(soup, 'confirmed cases')
        record['cases'] = self.getLeadingNumber(strings, '[0-9,]+ confirmed cases.')
        record['deaths'] = self.getLeadingNumber(strings, '[0-9,]+ deaths')

        # If not in first para, try looking for cases as "# - Positive cases"
        if record['cases'] is None:
            strings = self.findString(soup, 'Positive cases')
            record['cases'] = self.getLeadingNumber(strings, '[0-9,]+...Positive cases')

        # If not in first para, try looking for deaths as "# - Deaths"
        if record['deaths'] is None:
            strings = self.findString(soup, '[0-9,]+...Death')
            record['deaths'] = self.getLeadingNumber(strings, '[0-9,]+...Death')

        if record['cases'] is None:
            print('\n****** Failed to find the number of cases!')
            import pdb; pdb.set_trace()
            raise Exception('Failed to find the number of cases!')

        if record['deaths'] is None:
            print('\n****** WARNING - failed to find the number of deaths!')
        #     import pdb; pdb.set_trace()
        #     raise Exception('Failed to find the number of deaths!')

        strings = self.findString(soup, 'tests had been conducted')
        record['testsConducted'] = self.getLeadingNumber(strings, '[0-9,+*]+ tests had been conducted')

        # On 2020-04-23, the CDPH switched from reporting individual persons who have been tested
        # to reporting each test conducted. See https://www.cdph.ca.gov/Programs/OPA/Pages/NR20-062.aspx 
        strings = self.findString(soup, 'results have been received')
        if releaseDate < datetime.datetime(2020, 4, 23):
            record['testsReceived'] = self.getLeadingNumber(strings, '[0-9,+*]+ results have been received')
            record['testsPending'] = self.getLeadingNumber(strings, '[0-9,+*]+ are pending')
        elif releaseDate == datetime.datetime(2020, 4, 23):
            record['testsReceived'] = record['testsConducted']
            record['testsPending'] = 0

        self.data[url] = record

        self.printRecord(record)

    def findString(self, soup, regex):
        regex = '[\s]+'.join(regex.split(' '))
        strings = soup.find_all(string=re.compile(regex))
        if strings:
            newStrings = []
            for string in strings:
                output = ''
                for child in string.parent.children:
                    try:
                        if child.string is not None:
                            output += child.string
                        else:
                            if child.name == 'br':
                                output += ' '
                    except:
                        pass
                newStrings.append(output)
            strings = newStrings
            strings = [unicodedata.normalize('NFKD', string) for string in strings]
            strings = [' '.join(string.split()) for string in strings]
        return strings

    def getLeadingNumber(self, strings, regex):
        if not strings:
            return
        badCharPattern = re.compile('[+*,]')
        string = re.search(regex, strings[0])
        if not string:
            return
        string = badCharPattern.sub('', string[0])
        value = int(string.split(' ')[0])

        return value

    def saveData(self, path):
        filename = os.path.join(path, 'califData.pickle')
        print(f'\nSaving data to {filename} ...')
        output = {'saveDateTime': datetime.datetime.now(), 'data': self.data}
        with open(filename, 'wb') as f:
            pickle.dump(output, f)

    def loadData(self, path):
        filename = os.path.join(path, 'califData.pickle')
        if os.path.exists(filename):
            print(f'\nLoading data from {filename} ...')
            f = open(filename, 'rb')
            data = pickle.load(f)
            self.data = data['data']
        else:
            print('No data file!')

    def writeCsv(self, path):
        data = self.dataToNumpy()
        filename = os.path.join(path, 'califData.csv')
        print(f'\nExporting data to {filename} ...')
        with open(filename, 'wt') as f:
            f.write('date,releaseNumber,cases,deaths,testsConducted,testsReceived,testsPending\n')
            dateUrlList = sorted([(self.data[url]['releaseDate'], url) for url in self.data.keys()])
            for releaseDate, url, in dateUrlList:
                record = self.data[url]
                output = []
                output.append(record['releaseDate'].strftime('%Y-%m-%d'))
                output.append(record['releaseNumber'])
                for field in ['cases', 'deaths', 'testsConducted', 'testsReceived', 'testsPending']:
                    if record[field] is not None:
                        output.append(str(record[field]))
                    else:
                        output.append('')
                f.write(','.join(output) + '\n')

    def getNewestRecord(self):
        dateUrlList = sorted([(self.data[url]['releaseDate'], url) for url in self.data.keys()])
        return self.data[dateUrlList[-1][1]]

    def printRecord(self, record):
        output = f"Date: {record['releaseDate'].strftime('%Y-%m-%d')} ({record['releaseNumber']}) - "
        output += f"Cases: {record['cases']}, Deaths: {record['deaths']}, "
        output += f"Tests: {record['testsConducted']} (Received: {record['testsReceived']} / Pending: {record['testsPending']})"
        print(output)

    def dataToNumpy(self):
        dateUrlList = sorted([(self.data[url]['releaseDate'], url) for url in self.data.keys()])
        output = np.zeros(len(dateUrlList), dtype=[('date', 'datetime64[us]'), ('cases', 'f8'), ('deaths', 'f8'), ('testsConducted', 'f8'), ('testsReceived', 'f8'), ('testsPending', 'f8')])
        for i, (releaseDate, url) in enumerate(dateUrlList):
            record = self.data[url]
            output[i]['date'] = releaseDate
            output[i]['cases'] = record['cases'] if record['cases'] is not None else float('nan')
            output[i]['deaths'] = record['deaths'] if record['cases'] is not None else float('nan')
            output[i]['testsConducted'] = record['testsConducted'] if record['cases'] is not None else float('nan')
            output[i]['testsReceived'] = record['testsReceived'] if record['cases'] is not None else float('nan')
            output[i]['testsPending'] = record['testsPending'] if record['cases'] is not None else float('nan')

        return output


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataPath', default='./data')
    parser.add_argument('--force', action='store_true', help='Force reload of all data')
    args = parser.parse_args()

    cdphData = CdphCovidData()
    cdphData.loadData(args.dataPath)
    print(f'\nQuerying CDPH website: {cdphData.newsReleaseUrl}')
    cdphData.getData(force=args.force)
    cdphData.saveData(args.dataPath)
    cdphData.writeCsv(args.dataPath)
    