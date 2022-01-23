'''
Clean and process data from HU CSSE (https://github.com/CSSEGISandData/COVID-19) for use in Covid Visualisation Dashboard
'''

# imports
import os
import subprocess
import pandas as pd
import numpy as np


pd.set_option('mode.chained_assignment', None)

# set local filepaths for raw data csv's  and processed files as variables
daily_reports_filepath = 'H:/COVID-19/csse_covid_19_data/csse_covid_19_daily_reports'
# daily_reports_filepath_us = 'H:/COVID-19/csse_covid_19_data/csse_covid_19_daily_reports_us'
# time_series_filepath = 'H:/COVID-19/csse_covid_19_data/csse_covid_19_time_series'
LUT_filepath = 'H:/COVID-19/csse_covid_19_data'
processed_files_filepath = 'H:/Covid19Dashboard'

#%%
# navigate to directory with COVID repo

gitDir = 'H:/COVID-19'
os.chdir(gitDir)

# update repo from remote
cmd = 'git pull origin'
try:
    p1 = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p1.wait()
    print("Repo updated")
except:
    print('Git pull failed')

#%%

# load IUD Lookup table into DF for extraction of population, Lat and Long values
lut_df = pd.read_csv(LUT_filepath + '/UID_ISO_FIPS_LookUp_Table.csv')

# need the Combined Key for joining, then population, lat and long
lut_df = lut_df.rename(columns={'Long_': 'Long'})
lut_df = lut_df[['Combined_Key', 'Population', 'Lat', 'Long']]

# A typo in the 'Northwest Territories, Canada' entry of the LUT needs to be fixed to get the populations for
# that region (add a space after the comma)
# lut_df[lut_df['Combined_Key']=='Northwest Territories,Canada'].index
lut_df.iloc[762, 0] = 'Northwest Territories, Canada'

#%%
# Iterate through files in csse_daily_reports and generate extract data to Covid_raw_df (see Preprocessing_readme.md)

# set columns for df
initial_columns = ['Province_State', 'Country_Region', 'Confirmed', 'Deaths', 'Active']

# create empty df
covid_raw = pd.DataFrame()

# frames = [ process_your_file(f) for f in files ]
# result = pd.concat(frames)

for file in os.listdir(daily_reports_filepath):
    if file.endswith('v'):  # csv files only, ignore '.gitignore' and 'Preprocessing_readme.md'
        file_date = file.rstrip(".csv")  # remove '.csv' to use filename in Date column
        filedb = pd.read_csv(daily_reports_filepath + '/' + file)  # temp db to extract data from each file

        # add/rename columns based on number of columns in input files
        # no additional manipulation need when csv has 12 or 14 cols
        if filedb.count(axis='columns').max() == 8:
            # Set unreported active cases = None, better than 0 for unreported dates
            filedb['Active'] = None
            # rename columns to create uniform naming
            filedb = filedb.rename(columns={'Province/State': 'Province_State', 'Country/Region': 'Country_Region'})
        elif filedb.count(axis='columns').max() == 6:
            # Set unreported Active cases to None,
            filedb['Active'] = None
            # rename cols to uniform naming
            filedb = filedb.rename(columns={'Province/State': 'Province_State', 'Country/Region': 'Country_Region'})

        # group raw data by country and province/state
        filedb = filedb[initial_columns].groupby(
            ['Country_Region', 'Province_State'],
            as_index=False, dropna=False).agg({'Confirmed': 'sum', 'Deaths': 'sum', 'Active': 'sum'})
        # add Date column
        filedb['Date'] = pd.to_datetime(file_date, format='%m-%d-%Y')

        # add data to covid_raw df
        covid_raw = pd.concat([covid_raw, filedb], ignore_index=True, copy=False)
#%%
print(covid_raw.head())
#%%
# Clean the Covid raw table to remove rows with no Lat/Long value in the population LUT (see Preprocessing_readme.md)

'''Start by excluding cases reported on cruise ships  ~4000 rows, and ~200-300 cases
3 cruise ships: Grand Princess, Diamond Princess, MS Zaandam
also excluding cases reported for Summer Olympics 2020 ~700 rows (~865 cases)'''

dropped_rows = covid_raw['Province_State'].str.contains('Grand Princess') | \
               covid_raw['Province_State'].str.contains('Diamond Princess') | \
               covid_raw['Province_State'].str.contains('Cruise Ship') | \
               covid_raw['Country_Region'].str.contains('Grand Princess') | \
               covid_raw['Country_Region'].str.contains('Diamond Princess') | \
               covid_raw['Country_Region'].str.contains('MS Zaandam') | \
               covid_raw['Country_Region'].str.contains('Summer Olympics 2020')

covid_cleaned = covid_raw[~dropped_rows]

# Replace 'Mainland China' and 'Macau' entries in Country Region with 'China'
covid_cleaned['Country_Region'] = covid_cleaned['Country_Region'].replace(
    to_replace=['Mainland China', 'Macau'], value='China')

'''Next, remove rows with 'Unknown' 'Recovered','Repatriated Travellers','Port Quarantine' 
and 'External territories' in Province_State column. Setting those values to None will allow them to be 
grouped as countrywide tallies'''

exclusions = ['Unknown', 'Recovered', 'Repatriated Travellers', 'Port Quarantine', 'External territories']
covid_cleaned['Province_State'] = covid_cleaned['Province_State'].replace(to_replace=exclusions, value=None)

''' Next, where possible, modify values in Province_State or Country_Region so that the concatenation 
of those columns in the Combined_Key column will match values in the LUT
'''

# Replace 'South Korea' in Country_Region with 'Korea, South'
covid_cleaned.loc[:, 'Country_Region'] = covid_cleaned['Country_Region'].replace(
    to_replace='South Korea', value='Korea, South')

# Replace 'Hong Kong' with 'China' in country_region
covid_cleaned['Country_Region'] = covid_cleaned['Country_Region'].replace(to_replace='Hong Kong', value='China')

# Replace 'Iran (Islamic Republic of)' with 'Iran' in country_region
covid_cleaned.loc[:, 'Country_Region'] = covid_cleaned['Country_Region'].replace(
    to_replace='Iran (Islamic Republic of)', value='Iran')

# Replace 'UK' with 'United Kingdom' in country_region
covid_cleaned.loc[:, 'Country_Region'] = covid_cleaned['Country_Region'].replace(to_replace='UK',
                                                                                 value='United Kingdom')

# Replace 'London ON' and 'Toronto ON' with 'Ontario' in Province_State
covid_cleaned.loc[:, 'Province_State'] = covid_cleaned['Province_State'].replace(
    to_replace=['London, ON', 'Toronto, ON'], value='Ontario')

# several countries have same value in Province/State and Country eg Denmark Denmark
# Drop 'Denmark', 'France', 'Netherlands','Taiwan', 'UK', 'United Kingdom' from Province_State column only
Province_country_doubles = ['Denmark', 'France', 'Netherlands', 'Taiwan', 'UK', 'United Kingdom']
covid_cleaned.loc[:, 'Province_State'] = covid_cleaned['Province_State'].replace(
    to_replace=Province_country_doubles, value='')

# concat state_province with country where not null or empty string, else, just use country value

covid_cleaned.loc[:, 'Combined_Key'] = np.where(
    (covid_cleaned['Province_State'].isna()) | (covid_cleaned['Province_State'] == ''),
    covid_cleaned['Country_Region'], covid_cleaned['Province_State'] + ', ' + covid_cleaned['Country_Region'])

# join lut with covid cleaned to  get population, Lat and Long data
covid_cleaned = covid_cleaned.join(lut_df.set_index('Combined_Key'), on='Combined_Key')

# add incidence rate and case fatality % columns
covid_cleaned.loc[:, 'Incidence_Rate'] = covid_cleaned['Confirmed'] / (covid_cleaned['Population'] / 100000)
covid_cleaned.loc[:, 'Case_Fatality_pc'] = covid_cleaned['Deaths'] / covid_cleaned['Confirmed'] * 100

'''Despite cleaning, a small number of rows still lack Lat/Long values. Due to the small number of rows, and 
small numbers of cases in those rows, these will be dropped from the covid_cleaned'''
# drop remaining rows where lat isna
rows_to_drop = list(covid_cleaned[covid_cleaned['Lat'].isna()].index)
covid_cleaned = covid_cleaned.drop(index=rows_to_drop)

# arrange cols to match the sql Table
final_column_order = ['Date', 'Province_State', 'Country_Region', 'Lat', 'Long', 'Confirmed', 'Deaths', 'Active',
                      'Combined_Key', 'Population', 'Incidence_Rate', 'Case_Fatality_pc']

covid_cleaned = covid_cleaned[final_column_order]

#%%
# Group Covid Cleaned by Country and Date to get values for each date, calculate New cases and Deaths each day

# import base columns from covid_cleaned
country_daily = covid_cleaned.copy()

# convert Date column to datetime
country_daily.loc[:, 'Date'] = pd.to_datetime(country_daily.Date)  # might not need this....
# sort by date and Country, calculate sum of confirmed, deaths and active cases
country_daily = country_daily[['Date', 'Country_Region', 'Confirmed', 'Deaths', 'Active']].groupby(
    ['Date', 'Country_Region'], as_index=False).agg({'Confirmed': 'sum', 'Deaths': 'sum', 'Active': 'sum'}).sort_values(
    ['Country_Region', 'Date'], ignore_index=True)

# add columns for New_cases and New_deaths
country_daily.loc[:, 'New_cases'] = country_daily.sort_values(['Country_Region', 'Date']
                                                              ).groupby(['Country_Region']
                                                                        )['Confirmed'].apply(lambda x: x - x.shift(1))

country_daily.loc[:, 'New_deaths'] = country_daily.sort_values(['Country_Region', 'Date']
                                                               ).groupby(['Country_Region']
                                                                         )['Deaths'].apply(lambda x: x - x.shift(1))

# group by country to get country_latest df with latest value for each country

# import base columns from country_daily
country_latest = country_daily.copy()

# select columns to import from covid_cleaned
columns_to_import = ['Country_Region', 'Confirmed', 'Deaths', 'Active', 'New_cases']
# group by Country_region to get latest results for each country
country_latest = country_latest[columns_to_import].groupby(['Country_Region'], as_index=False).last()
# add deaths/100 cases column
country_latest.loc[:, 'Deaths_per_100'] = country_latest['Deaths'] / (country_latest['Confirmed'] / 100)
# get population data from lookuptable
country_latest = country_latest.join(lut_df.set_index('Combined_Key'), on='Country_Region')
# cases/million people
country_latest.loc[:, 'Cases_per_million'] = country_latest['Confirmed'] / (country_latest['Population'] / 1000000)

# values in country_latest are most recent case numbers
# create temp df to get case numbers and deaths from 1 week prior
tempdf = country_daily[['Country_Region', 'Confirmed', 'Deaths']].groupby('Country_Region', as_index=False).nth(-8)
tempdf = tempdf.rename(columns={'Country_Region': 'Country_Region',
                                'Confirmed': 'Confirmed_last_week',
                                'Deaths': 'Deaths_last_week'})

# join temp df with country_latest on country
country_latest = country_latest.join(tempdf.set_index('Country_Region'), on='Country_Region')
# calculate 1 week change
country_latest.loc[:, 'New_cases_last_week'] = (country_latest['Confirmed'] - country_latest['Confirmed_last_week'])
country_latest.loc[:, 'New_deaths_last_week'] = (country_latest['Deaths'] - country_latest['Deaths_last_week'])

# create temp df to get case numbers from 1 month prior
tempdf = country_daily[['Country_Region', 'Confirmed', 'Deaths']].groupby('Country_Region', as_index=False).nth(-29)
tempdf = tempdf.rename(columns={'Country_Region': 'Country_Region',
                                'Confirmed': 'Confirmed_last_month',
                                'Deaths': 'Deaths_last_month'})

# join temp df with country_latest on country
country_latest = country_latest.join(tempdf.set_index('Country_Region'), on='Country_Region')
# calculate 1 month change
country_latest.loc[:, 'New_cases_last_month'] = (country_latest['Confirmed'] - country_latest['Confirmed_last_month'])
country_latest.loc[:, 'New_deaths_last_month'] = (country_latest['Deaths'] - country_latest['Deaths_last_month'])

#%%
# daily_total df = Group all country data together to get a single set of values for each date

# import columns from country_daily table
daily_total = country_daily.copy()

# group by date, calculate sum of cases, deaths
daily_total = daily_total[['Date', 'Confirmed', 'Deaths', 'Active', 'New_cases']].groupby('Date').sum()
# add deaths/100 cases column
daily_total.loc[:, 'Deaths_per_100'] = daily_total['Deaths'] / (daily_total['Confirmed'] / 100)

# create tempdf to get number of countries at each date
tempdf = country_daily[['Date']]
# the number of countries with active case each day equals the value_count for given date
tempdf = tempdf.aggregate(['value_counts'])
# flatten teh heirachial index created by the aggregate function
tempdf.columns = tempdf.columns.to_flat_index()
# rename value_count column
tempdf.columns = ['No_countries']

# join the temp df to daily_total on 'Date' column
daily_total = daily_total.join(tempdf, on='Date')
daily_total = daily_total.reset_index()

#%%
# create csv files for each df
covid_cleaned.to_csv(processed_files_filepath + '/covid_cleaned.csv')
country_daily.to_csv(processed_files_filepath + '/country_daily.csv')
country_latest.to_csv(processed_files_filepath + '/country_latest.csv')
daily_total.to_csv(processed_files_filepath + '/daily_total.csv')
