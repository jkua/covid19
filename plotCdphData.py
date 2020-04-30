#!/usr/bin/env python3

import os
import datetime

import numpy as np
import matplotlib.pyplot as plt

from getCdphData import CdphCovidData

def movingAverage(a, n=7) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def interpolateMissingData(data):
    idx = np.where(np.isnan(data))[0]
    for i in idx:
        if (i > 0) and (i < (len(data)-1)):
            data[i] = (data[i-1] + data[i+1])/2
        elif i > 0:
            data[i] = data[i-1]
        elif i < (len(data)-1):
            data[i] = data[i+1]

def savePlot(fig, path, filename, dpi=100):
    filename = os.path.join(path, filename)
    print(f'\nSaving plot to {filename}')
    fig.savefig(filename, dpi=dpi)

def convertNumpyDatetimeToDatetime(dt, utcOffset=-8):
    timestamp = (dt-np.datetime64('1970-01-01T00:00:00')-utcOffset*3600*1000000)/np.timedelta64(1, 's')
    return datetime.datetime.fromtimestamp(timestamp)


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataPath', default='./data')
    parser.add_argument('--plotsPath', default='./plots')
    parser.add_argument('--noPlot', action='store_true')
    args = parser.parse_args()

    cdphData = CdphCovidData()
    cdphData.loadData(args.dataPath)
    
    bayAreaSip = datetime.datetime(2020, 3, 17)
    californiaSip = datetime.datetime(2020, 3, 20)
    switchFromIndividualTestsToAllTests = datetime.datetime(2020, 4, 22)

    data = cdphData.dataToNumpy()
    newCases = np.diff(data['cases'])
    newTestsReceived = np.diff(data['testsReceived'])

    interpolateMissingData(data['cases'])
    interpolateMissingData(data['deaths'])

    newestRecord = cdphData.getNewestRecord()
    casesPerTest = newestRecord['cases']/newestRecord['testsReceived']
    deathsPerCase = newestRecord['deaths']/newestRecord['cases']

    print('\nCalifornia (CDPH)')
    print('--------------------')
    cdphData.printRecord(newestRecord)
    print(f'Case fatality rate (*): {deathsPerCase*100:.3f} %')
    print(f'Cases per test received: {casesPerTest:.3f}')
    print('\n* the case fatality rate estimate uses all cases rather than closed cases due to recovered case counts not being available')

    fig, axes = plt.subplots(4, sharex=True, figsize=(6, 10))
    fig.suptitle('California (CDPH)')
    for i, field in enumerate(['cases', 'deaths']):
        axes[i].plot(data['date'], data[field])
        axes[i].set_title(field.title())
        axes[i].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
        axes[i].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
        axes[i].set_ylim([10, None])
        axes[i].set_yscale('log')

    axes[2].plot(data['date'][1:], np.diff(data['cases']))
    axes[2].plot(data['date'][4:-3], movingAverage(np.diff(data['cases'])), color='k', linestyle=':')
    axes[2].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[2].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[2].set_ylim([0, None])
    axes[2].set_title('New Cases')
    
    axes[3].plot(data['date'][1:], np.diff(data['deaths']))
    axes[3].plot(data['date'][4:-3], movingAverage(np.diff(data['deaths'])), color='k', linestyle=':')
    axes[3].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[3].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[3].set_ylim([0, None])
    axes[3].set_title('Daily Deaths')
    fig.autofmt_xdate()
    fig.subplots_adjust(left=0.1, bottom=0.07, right=0.94, top=0.93, wspace=None, hspace=0.15)
    savePlot(fig, args.plotsPath, 'cdph_ca_cases.png')

    fig, axes = plt.subplots(2, sharex=True, figsize=(6, 8))
    fig.suptitle('California (CDPH)')
    for i, field in enumerate(['testsConducted', 'testsReceived', 'testsPending']):
        axes[0].plot(data['date'], data[field], label=field.replace('tests', ''))
    axes[0].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[0].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[0].axvspan(convertNumpyDatetimeToDatetime(data['date'][0]), switchFromIndividualTestsToAllTests, color='k', linewidth=0, alpha=0.1)
    axes[0].set_xlim([convertNumpyDatetimeToDatetime(data['date'][0]), None])
    axes[0].set_ylim([0, None])
    axes[0].legend(loc='upper left')
    axes[0].set_title('Tests')

    # axes[1].plot(data['date'], data['cases'])
    # axes[1].set_title('Cases')
    # axes[1].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    # axes[1].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    # axes[1].set_ylim([10, None])
    # axes[1].set_yscale('log')

    axes[1].plot(data['date'][1:], np.diff(data['cases']), label='New Cases')
    axes[1].plot(data['date'][1:], np.diff(data['testsReceived']), label='New Tests Rcvd')
    axes[1].plot(data['date'][14:-3], movingAverage(np.diff(data['testsReceived'][10:])), color='k', linestyle=':')
    axes[1].legend(loc='upper left')
    axes[1].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[1].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[1].axvspan(convertNumpyDatetimeToDatetime(data['date'][1]), switchFromIndividualTestsToAllTests, color='k', linewidth=0, alpha=0.1)
    axes[1].set_xlim([convertNumpyDatetimeToDatetime(data['date'][1]), None])
    axes[1].set_ylim([0, np.max(movingAverage(np.diff(data['testsReceived'][10:])))*1.1])
    axes[1].set_title('New Cases vs New Tests')
    fig.autofmt_xdate()
    fig.subplots_adjust(left=0.13, bottom=0.10, right=0.94, top=0.91, wspace=None, hspace=0.15)
    savePlot(fig, args.plotsPath, 'cdph_ca_tests.png')

    if not args.noPlot:
        plt.show()

    
