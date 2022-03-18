# Covid Cleaning Dashboard
Raw data from JHU CSSE (https://github.com/CSSEGISandData/COVID-19) is 
processed into 4 Tables which will be the basis of the data visualisation 
dashboard

This visualisation only uses data in the global daily_reports for now. 
The daily_reports data includes data from the US, but does not include 
data on testing rates and hospitalisation rates included in the 
daily_reports_us files. 

(I plan to find vacination data to add in later .... https://github.com/govex/COVID-19.git)

## DataCleaning.py
#### Look up tables
IUD_ISO LUT in CSSE Repo contains iso3 code, longitude, latitude and population
data \

A second continent LUT from https://statisticstimes.com/geography/countries-by-continents.php
has iso3 codes and continent data.
The two tables are combined to give a single df with columns:
 - iso3 (3 letter country code)
 - Combined_Key (State/Province, Country)
 - Population
 - Lat
 - Long
 - Continent
#### Covid_Raw df
Iterate through files in JHU Repo, extract Date, province/State, 
Country/Region, deaths and active case numbers. 
(Not collecting Recovered case numbers for recovered cases was pulled 
from JHU data repository in August 2021)

#### Covid_preprocessed df
Clean the Covid raw table to remove rows with no Lat/Long 
values in the population LUT. \
concat Province_State with Country_Region to create \
Combined_key column \
Join LUT on combined_key to get Continent, Lat, Long and population values. \
Add Incidence_rate column (Number of cases /100,000 population) \
Add Case_Fatality_pc column (Deaths / Confirmed (*100))\
Final columns:
- 'Date', 
- 'Province_State', 
- 'Country_Region', 
- 'Continent', 
- 'Lat', 
- 'Long', 
- 'Confirmed', 
- 'Deaths',
- 'Active', 
- 'Combined_Key', 
- 'Population', 
- 'Incidence_Rate', 
- 'Case_Fatality_pc'

#### Country_daily df
Start with copy of covid_cleaned \
sorty by date, and Province_state so that when grouping by country, all provinces of the
country will have the correct continent value (for example, Reunion, France will appear in Europe
instead of Africa)
Group by Date, Country to get values for each date. \
Get last continent value for each country \
Calculate sum of cases and deaths on each date. \
Add columns for New cases and New Deaths each day 
Join with LUT to get geographical data (iso3, lat long population)\
Final columns:
- Date
- Confirmed
- Deaths
- Active
- New_cases
- iso3
- population
- lat
- long
- continent

#### Country_latest df
Group by country to get current values for each country, 
add columns to with confirmed and deaths values 1 week ago and 
1 month ago. \
Add column for deaths/100 cases\
join population lut to get population values for each country\
Add column for cases/million in people\
Final columns:
- Country_Region
- Confirmed
- Deaths
- Active
- Deaths_per_100
- iso3
- population
- Lat
- Long
- Continent
- Cases_per_million
- Confirmed_last_week (number of cases 1 week ago)
- Deaths_last_week (number of deaths 1 week ago)
- New_cases_last_week (number of cases reported in the last week)
- New_deaths_last_week (number of deaths reported in the last week)
- Confirmed_last_month (number of cases 1 month ago)
- Deaths_last_month (number of deaths 1 month ago)
- New_cases_last_month (number of cases reported in the last month)
- New_deaths_last_month (number of deaths reported in the last month)

#### Daily_total df
Starting from country_daily, group all country data together 
to get a single set of values for each date.\
Add column to count number of countries contributing each day\
Final columns:
- Date
- Confirmed
- Deaths
- Active
- New_cases
- New_deahts
- Deaths_per_100
- No_countries