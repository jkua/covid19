#!/usr/bin/env python3

import os
import pickle
import datetime

import numpy as np
import matplotlib.pyplot as plt

from plotCdphData import movingAverage, savePlot


def dateParser(d_bytes):
    s = d_bytes.decode('utf-8')
    return np.datetime64(datetime.datetime.strptime(s, '%Y-%m-%d'))

class NytData(object):
    def __init__(self, path):
        self.path = path
        self.countiesFilename = os.path.join(path, 'us-counties.csv')
        self.statesFilename = os.path.join(path, 'us-states.csv')
        self.filenames = [self.countiesFilename, self.statesFilename]

    def loadSource(self):
        self.loadCounties()
        self.loadStates()
        
    def loadCounties(self):
        f = open(os.path.join(self.path, 'us-counties.csv'), 'rt')
        names = f.readline().strip()
        self.countiesData = np.genfromtxt(f, delimiter=',', names=names, dtype=[('date', 'datetime64[us]'), ('county', 'U64'), ('state', 'U64'), ('fips', 'u4'), ('cases', 'i4'), ('deaths', 'i4')], converters={0:dateParser})

    def loadStates(self):
        f = open(os.path.join(self.path, 'us-states.csv'), 'rt')
        names = f.readline().strip()
        self.statesData = np.genfromtxt(f, delimiter=',', names=names, dtype=[('date', 'datetime64[us]'), ('state', 'U64'), ('fips', 'u4'), ('cases', 'i4'), ('deaths', 'i4')], converters={0:dateParser})

    def modificationTime(self):
        return max([os.path.getmtime(path) for path in self.filenames])

    def getState(self, name, startDate=None):
        idx = self.statesData['state'] == name
        if startDate:
            idx = idx & (self.statesData['date'] >= startDate)
        return self.statesData[idx]

    def getStatesSum(self, states=None, startDate=None):
        if not states:
            states = np.unique(self.statesData['state'])
        dates = np.unique(self.statesData['date'])
        data = np.zeros(len(dates), dtype=[('date', 'datetime64[us]'), ('cases', 'i4'), ('deaths', 'i4')])
        data['date'] = dates
        fields = ['cases', 'deaths']
        for state in states:
            stateData = self.getState(state)
            for i, d in enumerate(stateData['date']):
                j = data['date'] == d
                for field in fields:
                    data[field][j] = data[field][j] + stateData[field][i]
        if startDate:
            idx = data['date'] >= startDate
        return data[idx]

    def getCounty(self, county, state, startDate=None):
        idx = (self.countiesData['county'] == county) & (self.countiesData['state'] == state)
        if startDate:
            idx = idx & (self.countiesData['date'] >= startDate)
        return self.countiesData[idx]

    def getCountiesSum(self, counties, state, startDate=None):
        dates = np.unique(self.countiesData['date'])
        data = np.zeros(len(dates), dtype=[('date', 'datetime64[us]'), ('cases', 'i4'), ('deaths', 'i4')])
        data['date'] = dates
        fields = ['cases', 'deaths']
        for county in counties:
            countyData = self.getCounty(county, state)
            for i, d in enumerate(countyData['date']):
                j = data['date'] == d
                for field in fields:
                    data[field][j] = data[field][j] + countyData[field][i]
        if startDate:
            idx = data['date'] >= startDate
        return data[idx]

    def newCases(self, data):
        return np.diff(data['cases'])

    def dailyDeaths(self, data):
        return np.diff(data['deaths'])


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataPath', default='./data')
    parser.add_argument('--plotsPath', default='./plots')
    parser.add_argument('--noPlot', action='store_true')
    args = parser.parse_args()

    nytData = NytData(os.path.join(args.dataPath, 'nytimes'))

    nytData.loadSource()

    startDate = datetime.datetime(2020, 2, 22)
    bayAreaSip = datetime.datetime(2020, 3, 17)
    californiaSip = datetime.datetime(2020, 3, 20)

    california = nytData.getState('California', startDate)
    # counties = ['Alameda', 'Contra Costa', 'Marin', 'Napa', 'San Francisco', 'San Mateo', 'Santa Clara', 'Solano', 'Sonoma']
    counties = ['Alameda', 'Contra Costa', 'San Francisco', 'San Mateo', 'Santa Clara']
    bayArea = nytData.getCountiesSum(counties, 'California', startDate)
    losAngeles = nytData.getCounty('Los Angeles', 'California', startDate)
    countyData = {county: nytData.getCounty(county, 'California', startDate) for county in counties}

    fields = ['cases', 'deaths', 'new cases', 'daily deaths']   
    unitedStates = nytData.getStatesSum(startDate=startDate)
    states = ['California', 'New York', 'New Jersey', 'Washington', 'Florida', 'Louisiana', 'Michigan', 'Georgia']
    stateData = {state: nytData.getState(state, startDate) for state in states}
    fig, axes = plt.subplots(len(fields), sharex=True, figsize=(7, 10))
    fig.suptitle('United States (NYT)')
    for ax, field in zip(axes, fields):
        if field == 'new cases':
            ax.plot(unitedStates['date'][1:], nytData.newCases(unitedStates), 'r.-', linewidth=3, label='United States')
            ax.plot(unitedStates['date'][4:-3], movingAverage(nytData.newCases(unitedStates)), color='k', linestyle=':')
            for state in states:
                ax.plot(stateData[state]['date'][1:], nytData.newCases(stateData[state]), '.-', label=state)
        elif field == 'daily deaths':
            ax.plot(unitedStates['date'][1:], nytData.dailyDeaths(unitedStates), 'r.-', linewidth=3, label='United States')
            ax.plot(unitedStates['date'][4:-3], movingAverage(nytData.dailyDeaths(unitedStates)), color='k', linestyle=':')
            for state in states:
                ax.plot(stateData[state]['date'][1:], nytData.dailyDeaths(stateData[state]), '.-', label=state)
        else:
            ax.plot(unitedStates['date'], unitedStates[field], 'r', linewidth=3, label='United States')
            for state in states:
                ax.plot(stateData[state]['date'], stateData[state][field], label=state)
            ax.set_ylim([10, None])
            ax.set_yscale('log')
        ax.axvline(californiaSip, color='k', linewidth=1, linestyle='--')
        ax.set_xlim([startDate, None])
        ax.legend(bbox_to_anchor=(1.04,1), loc="upper left")
        ax.set_title(field.title())
    fig.autofmt_xdate()
    fig.subplots_adjust(left=0.1, bottom=0.07, right=0.72, top=0.93, wspace=None, hspace=0.15)
    savePlot(fig, args.plotsPath, 'nyt_us_cases.png')

    fig, axes = plt.subplots(len(fields), sharex=True, figsize=(7, 10))
    fig.suptitle('California (NYT)')
    for ax, field in zip(axes, fields):
        if field == 'new cases':
            ax.plot(california['date'][1:], nytData.newCases(california), '.-', linewidth=3, label='California')
            ax.plot(california['date'][4:-3], movingAverage(nytData.newCases(california)), color='k', linestyle=':')
            ax.plot(losAngeles['date'][1:], nytData.newCases(losAngeles), '.-', linewidth=3, label='Los Angeles')
            ax.plot(bayArea['date'][1:], nytData.newCases(bayArea), '.-', linewidth=3, label='Bay Area')
            for county in counties:
                ax.plot(countyData[county]['date'][1:], nytData.newCases(countyData[county]), '.-', label=county)
        elif field == 'daily deaths':
            ax.plot(california['date'][1:], nytData.dailyDeaths(california), '.-', linewidth=3, label='California')
            ax.plot(california['date'][4:-3], movingAverage(nytData.dailyDeaths(california)), color='k', linestyle=':')
            ax.plot(losAngeles['date'][1:], nytData.dailyDeaths(losAngeles), '.-', linewidth=3, label='Los Angeles')
            ax.plot(bayArea['date'][1:], nytData.dailyDeaths(bayArea), '.-', linewidth=3, label='Bay Area')
            for county in counties:
                ax.plot(countyData[county]['date'][1:], nytData.dailyDeaths(countyData[county]), '.-', label=county)
        else:    
            ax.plot(california['date'], california[field], linewidth=3, label='California')
            ax.plot(losAngeles['date'], losAngeles[field], linewidth=3, label='Los Angeles')
            ax.plot(bayArea['date'], bayArea[field], linewidth=3, label='Bay Area')
            for county in counties:
                ax.plot(countyData[county]['date'], countyData[county][field], label=county)
            ax.set_ylim([10, None])
            ax.set_yscale('log')
        ax.axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
        ax.axvline(californiaSip, color='k', linewidth=1, linestyle='--')
        ax.set_xlim([startDate, None])
        ax.legend(bbox_to_anchor=(1.04,1), loc="upper left")
        ax.set_title(field.title())
    fig.autofmt_xdate()
    fig.subplots_adjust(left=0.1, bottom=0.07, right=0.72, top=0.93, wspace=None, hspace=0.15)
    savePlot(fig, args.plotsPath, 'nyt_ca_cases.png')

    if not args.noPlot:
        plt.show()


