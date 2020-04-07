#!/usr/bin/env python3

import os
import datetime

import numpy as np
import matplotlib.pyplot as plt

from getCdphData import CdphCovidData

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataPath', default='./data')
    args = parser.parse_args()

    cdphData = CdphCovidData()
    cdphData.loadData(args.dataPath)
    
    bayAreaSip = datetime.datetime(2020, 3, 17)
    californiaSip = datetime.datetime(2020, 3, 20)

    data = cdphData.dataToNumpy()
    newCases = np.diff(data['cases'])
    newTestsReceived = np.diff(data['testsReceived'])

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
    axes[2].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[2].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[2].set_ylim([0, None])
    axes[2].set_title('New Cases')
    
    axes[3].plot(data['date'][1:], np.diff(data['deaths']))
    axes[3].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[3].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[3].set_ylim([0, None])
    axes[3].set_title('Daily Deaths')
    fig.autofmt_xdate()
    fig.subplots_adjust(left=0.1, bottom=0.07, right=0.94, top=0.93, wspace=None, hspace=0.15)

    fig, axes = plt.subplots(3, sharex=True, figsize=(6, 10))
    fig.suptitle('California (CDPH)')
    for i, field in enumerate(['testsConducted', 'testsReceived', 'testsPending']):
        axes[0].plot(data['date'], data[field], label=field.replace('tests', ''))
    axes[0].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[0].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[0].set_ylim([0, None])
    axes[0].legend()
    axes[0].set_title('Tests')

    axes[1].plot(data['date'], data['cases'])
    axes[1].set_title('Cases')
    axes[1].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[1].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[1].set_ylim([10, None])
    axes[1].set_yscale('log')

    axes[2].plot(data['date'][1:], np.diff(data['cases']), label='New Cases')
    axes[2].plot(data['date'][1:], np.diff(data['testsReceived']), label='New Tests Rcvd')
    axes[2].legend()
    axes[2].axvline(bayAreaSip, color='r', linewidth=1, linestyle='--')
    axes[2].axvline(californiaSip, color='k', linewidth=1, linestyle='--')
    axes[2].set_ylim([0, None])
    axes[2].set_title('New Cases vs New Tests')
    fig.autofmt_xdate()
    fig.subplots_adjust(left=0.1, bottom=0.07, right=0.94, top=0.93, wspace=None, hspace=0.15)

    plt.show()

    
