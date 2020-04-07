# COVID-19 data plotting
This pulls data from Johns Hopkins CSSE and the New York Times and plots data for the United States, California, and the San Francisco Bay Area.

It also includes a scraper for the California Department of Public Health (CDPH) news releases to get the daily publication of case data. The file `data/califData.csv` is a periodically updated snapshot of that data.

## Requirements
1. Python 3
2. numpy
3. matplotlib
4. requests
5. beautifulsoup4

To install: `pip3 install -r requirements.txt`

## Instructions
1. `./updateData`
2. `./plotNytData.py`
3. `./plotCdphData.py`
