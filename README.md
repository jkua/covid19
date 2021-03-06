# COVID-19 data plotting
This pulls data from Johns Hopkins CSSE and the New York Times and plots data for the United States, California, and the San Francisco Bay Area.

It also includes a scraper for the California Department of Public Health (CDPH) news releases to get the daily publication of case data. The file `data/califData.csv` is a periodically updated snapshot of that data.

## Current plots
* Black dotted lines are a 7-day moving average
* Vertical black dashed line is the date of the CA shelter in place order
* Vertical red dashed line is the date of the SF Bay Area shelter in place order
![NYT US Cases](https://github.com/jkua/covid19/raw/master/plots/nyt_us_cases.png)
![NYT CA Cases](https://github.com/jkua/covid19/raw/master/plots/nyt_ca_cases.png)
![CDPH CA Cases](https://github.com/jkua/covid19/raw/master/plots/cdph_ca_cases.png)

* Grey area: before April 23rd, the CDPH reported tested persons. On April 23 and after, each individual test, regardless of the number per person, is reported. See [this release](https://www.cdph.ca.gov/Programs/OPA/Pages/NR20-062.aspx).
![CDPH CA Tests](https://github.com/jkua/covid19/raw/master/plots/cdph_ca_tests.png)

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
