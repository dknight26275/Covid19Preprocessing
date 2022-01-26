# Covid Cleaning Dashboard
Raw data from JHU CSSE (https://github.com/CSSEGISandData/COVID-19) is 
processed into 4 Tables which will be the basis of the data visualisation 
dashboard

This visualisation only uses data in the global daily_reports for now. 
The daily_reports data includes data from the US, but does not include 
data on testing rates and hospitalisation rates included in the 
daily_reports_us files. I may come back to those file for a more detailed 
analysis later.

(I need to find vacination data to add in.... https://github.com/govex/COVID-19.git)

## DataCleaning.py
#### Look up tables
IUD_ISO LUT in CSSE Repo contains iso3 code, longitude, latitude and population
data \

A second continent LUT from https://statisticstimes.com/geography/countries-by-continents.php
has iso3 codes and continent data.
#### Covid_Raw df
Iterate through files in JHU Repo, extract Date, province/State, 
Country, deaths and active case numbers. 
(Not collecting Recovered case numbers for recovered cases was pulled 
from JHU data repository in August 2021)

#### Covid_preprocessed df
Clean the Covid raw table to remove rows with no Lat/Long 
values in the population LUT. \
concat Province_State with Country_Region to create \
Combined_key column \
Join LUT on combined_key to get Continent, Lat, Long and population values. \
Add Incidence_rate column (Number of cases /100,000 population) \
Add Case_Fatality_pc column (Deaths / Confirmed (*100))

#### Country_daily df
Group Covid Cleaned by Date, Country and Continent to get values for each date. 
Calculate sum of cases and deaths on each date. \
Add columns for New cases and New Deaths each day

#### Country_latest df
Group by country to get current values for each country, 
add columns to with confirmed and deaths values 1 week ago and 
1 month ago. \
Add column for deaths/100 cases\
join population lut to get population values for each country\
Add column for cases/million in people

#### Daily_total df
Starting from country_daily, group all country data together 
to get a single set of values for each date.\
Add column to count number of countries contributing each day