# %% [markdown]
# ## Setup
# Shared imports, the Frost client ID and a helper function used by all tasks.
 
# %%
from pathlib import Path
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import requests
import yaml
 
#%%
# The client ID is read from a independent file.
CLIENT_ID = Path('frost_client_id.txt').read_text().strip()
ENDPOINT = 'https://frost.met.no/observations/v0.jsonld'
STATION = 'SN17850'  # Ås
YEAR = 2025
 
 
def fetch_frost(source: str, element: str, year: int) -> pd.DataFrame:
    """Fetch daily observations of one element from one Frost station for a whole year."""
    parameters = {
        'sources': source,
        'elements': element,
        # Frost intervals exclude the end date, so ending on 1 January includes 31 December
        'referencetime': f'{year}-01-01/{year + 1}-01-01',
    }
    response = requests.get(ENDPOINT, parameters, auth=(CLIENT_ID, ''), timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f'Frost request failed ({response.status_code}): {response.text}')
 
    # Build one table for all the observations
    rows = []
    for item in response.json()['data']:
        row = pd.DataFrame(item['observations'])
        row['referenceTime'] = item['referenceTime']
        row['sourceId'] = item['sourceId']
        rows.append(row)
 
    observations = pd.concat(rows, ignore_index=True)
    observations['referenceTime'] = pd.to_datetime(observations['referenceTime'])
    return observations
 
 
# %% [markdown]
# ## Task 1: Air temperature
 
# %%
df = fetch_frost(STATION, 'mean(air_temperature P1D)', YEAR)
# Frost gives two daily means: PT0H (midnight to midnight) and PT6H (06 UTC to 06 UTC).
# Keep only the calendar-day series, otherwise every day is counted twice.
df = df[df['timeOffset'] == 'PT0H']
print(f'{len(df)} days of temperature data')
print(df.head())
 
# %%
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df['referenceTime'], df['value'], color='tab:red', linewidth=1.2)
ax.axhline(0, color='grey', linewidth=0.8, linestyle='--')
ax.set_title(f'Daily mean air temperature, Ås ({STATION}), {YEAR}')
ax.set_xlabel('Date')
ax.set_ylabel('Temperature (°C)')
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.grid(alpha=0.3)
fig.tight_layout()
plt.show()
 
# %%
summary = df['value'].agg(['mean', 'median', 'min', 'max']).round(1)
summary.index = ['Mean', 'Median', 'Min', 'Max']
summary = summary.to_frame(name='Temperature (°C)')
print(f'\nAir temperature summary, Ås {YEAR}')
print(summary)
 
# %% [markdown]
# ## Task 2: Precipitation
# Daily precipitation is a *sum* per day and is often zero, so it is shown as **bars**.
# Temperature changes continuously, so it is shown as a **line**.
# The two measurements have different units and scales, so each gets its own y-axis
# (temperature on the left, precipitation on the right).
#
# Precipitation uses `timeOffset = PT18H`: each value is the total from 18 UTC the day before
# to 18 UTC on the date. This overlaps 18 of the 24 hours of the calendar day used for
# temperature (`PT0H`, midnight to midnight).
 
# %%
precip = fetch_frost(STATION, 'sum(precipitation_amount P1D)', YEAR)
precip = precip[precip['timeOffset'] == 'PT18H']
print(f'{len(precip)} days of precipitation data')
 
# Check for missing days by comparing against every date in the year
all_days = pd.date_range(f'{YEAR}-01-01', f'{YEAR}-12-31', freq='D', tz='UTC')
missing = all_days.difference(precip['referenceTime'])
print(f'Missing days: {list(missing.date)}')
 
# %%
fig, ax_temp = plt.subplots(figsize=(12, 5))
ax_rain = ax_temp.twinx()
 
ax_rain.bar(precip['referenceTime'], precip['value'], width=1, color='tab:blue', alpha=0.6,
            label='Precipitation (mm/day)')
ax_temp.plot(df['referenceTime'], df['value'], color='tab:red', linewidth=1.2,
             label='Mean temperature (°C)')
ax_temp.axhline(0, color='grey', linewidth=0.8, linestyle='--')
 
# Draw the temperature line in front of the bars
ax_temp.set_zorder(ax_rain.get_zorder() + 1)
ax_temp.patch.set_visible(False)
 
ax_temp.set_title(f'Daily mean temperature and precipitation, Ås ({STATION}), {YEAR}')
ax_temp.set_xlabel('Date')
ax_temp.set_ylabel('Temperature (°C)', color='tab:red')
ax_rain.set_ylabel('Precipitation (mm/day)', color='tab:blue')
ax_temp.tick_params(axis='y', labelcolor='tab:red')
ax_rain.tick_params(axis='y', labelcolor='tab:blue')
ax_temp.xaxis.set_major_locator(mdates.MonthLocator())
ax_temp.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax_temp.grid(alpha=0.3)
 
# One shared legend for both axes
lines_t, labels_t = ax_temp.get_legend_handles_labels()
lines_r, labels_r = ax_rain.get_legend_handles_labels()
ax_temp.legend(lines_t + lines_r, labels_t + labels_r, loc='upper left')
 
fig.tight_layout()
plt.show()
 
 
# %% [markdown]
# Task 3
 
# %%
# %% [markdown]
# ## Task 3: Historical temperature data
# The 2025 temperatures are compared with the same station 100 years earlier.
# To show both years on the same time axis, the old dates are moved forward 100 years.
# The values are unchanged; only the year in the date is shifted, so both lines run January to December.
 
# %%
YEAR_OLD = YEAR - 100
df_old = fetch_frost(STATION, 'mean(air_temperature P1D)', YEAR_OLD)
print(df_old['timeOffset'].value_counts())  # check which offsets exist before filtering
 
df_old = df_old[df_old['timeOffset'] == 'PT0H']
print(f'{len(df_old)} days of temperature data for {YEAR_OLD}')
 
# Same calendar day in both years, so the two lines can share the x-axis
df_old['plotTime'] = df_old['referenceTime'] + pd.DateOffset(years=YEAR - YEAR_OLD)
 
# %%
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df_old['plotTime'], df_old['value'], color='tab:blue', linewidth=1.2, label=str(YEAR_OLD))
ax.plot(df['referenceTime'], df['value'], color='tab:red', linewidth=1.2, label=str(YEAR))
ax.axhline(0, color='grey', linewidth=0.8, linestyle='--')  # freezing point
ax.set_title(f'Daily mean air temperature, Ås ({STATION}): {YEAR_OLD} vs {YEAR}')
ax.set_xlabel('Date')
ax.set_ylabel('Temperature (°C)')
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.grid(alpha=0.3)
ax.legend(loc='upper left')
fig.tight_layout()
plt.show()
 
# %%
stats = ['mean', 'median', 'min', 'max']
summary_compare = pd.DataFrame({
    f'{YEAR_OLD} (°C)': df_old['value'].agg(stats),
    f'{YEAR} (°C)': df['value'].agg(stats),
}).round(1)
# Round first, so the difference matches the numbers shown in the table
diff = summary_compare[f'{YEAR} (°C)'] - summary_compare[f'{YEAR_OLD} (°C)']
summary_compare['Difference (°C)'] = diff.round(1)
summary_compare.index = ['Mean', 'Median', 'Min', 'Max']
print(f'\nAir temperature summary, Ås {YEAR_OLD} vs {YEAR}')
print(summary_compare)
 
 
# %%
 
# %%
 
# %% [markdown]
# ## Task 4: Heatwaves
# In Norway a heatwave is five or more consecutive days with a maximum temperature of at least 27 °C.
# The function below fetches the daily maximum temperature (`max(air_temperature P1D)`) for any
# station and year, finds every run of consecutive hot days, and keeps the runs that last five days or more.
# A run is broken both by a day below 27 °C and by a missing day in the data.
# The result is written to a YAML file in the same format as the example file.
#
# The daily maximum uses `timeOffset = PT0H` (midnight to midnight), so each date only covers its own
# 24 hours. `PT18H` starts at 18 UTC the day before and can carry a warm evening over to the next date,
# which makes heatwaves look longer. `PT6H` mostly describes the afternoon of the previous day.
 
# %%
HEATWAVE_TEMP = 27.0  # °C
HEATWAVE_MIN_DAYS = 5
 
 
def count_heatwaves(station_id: str, station_name: str, year: int, filename: str) -> int:
    """Count heatwaves for one station and year, and write a summary to a YAML file."""
    max_temp = fetch_frost(station_id, 'max(air_temperature P1D)', year)
 
    # Use the calendar day (PT0H), so each date only covers its own 24 hours.
    # If the station does not have PT0H, fall back to the first available offset.
    offsets = sorted(max_temp['timeOffset'].unique())
    offset = 'PT0H' if 'PT0H' in offsets else offsets[0]
    max_temp = max_temp[max_temp['timeOffset'] == offset]
 
    # Keep only the hot days, in date order
    hot = max_temp[max_temp['value'] >= HEATWAVE_TEMP].sort_values('referenceTime')
 
    # A new run starts whenever the gap to the previous hot day is not exactly one day
    new_run = hot['referenceTime'].diff() != pd.Timedelta(days=1)
    run_id = new_run.cumsum()
    runs = hot.groupby(run_id)['referenceTime'].agg(start='min', end='max', days='size')
    heatwaves = runs[runs['days'] >= HEATWAVE_MIN_DAYS]
 
    dates = [
        f'{start:%Y-%m-%d} - {end:%Y-%m-%d}'
        for start, end in heatwaves[['start', 'end']].itertuples(index=False)
    ]
    summary = {
        'dates': dates,
        'station_id': station_id,
        'station_name': station_name,
        'year': year,
    }
    with open(filename, 'w') as file:
        yaml.dump(summary, file)
 
    return len(dates)
 
 
# %%
heatwave_file = f'heatwave_summary_{STATION}_{YEAR}.yml'
n_heatwaves = count_heatwaves(STATION, 'Ås', YEAR, heatwave_file)
print(f'{n_heatwaves} heatwaves in Ås in {YEAR}\n')
print(Path(heatwave_file).read_text())


# %%
# Task 5
# Function for calculating a 7-day moving average of the daily mean air temperature
def calculate_moving_average(df, column_name='value', window='7D'):
    """
    Calculate a 7-day moving average of the specified column.
    """
    return df[column_name].rolling(window=window).mean()

# Calculating the 7-day moving average for 2025 temperature data
df['referenceTime'] = pd.to_datetime(df['referenceTime'])
df = df.sort_values('referenceTime').reset_index(drop=True)

# add a new column for the 7-day moving average
df['temp_7d_ma'] = calculate_moving_average(df, column_name='value', window=7)

# 3. Plot
fig, ax = plt.subplots(figsize=(12, 6))

# Daily temperature as scatter plot
ax.scatter(
    df['referenceTime'], 
    df['value'], 
    color='tab:blue', 
    alpha=0.4, 
    s=20, 
    label='Daily Temperature'
)

# 7-day moving average as line
ax.plot(
    df['referenceTime'], 
    df['temp_7d_ma'], 
    color='tab:red', 
    linewidth=2, 
    label='7-Day Moving Average'
)

# Plot formatting
ax.set_title('Daily Temperatures and 7-Day Moving Average (2025)', fontsize=14, fontweight='bold')
ax.set_xlabel('Date', fontsize=11)
ax.set_ylabel('Temperature (°C)', fontsize=11)
ax.axhline(0, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='upper left', frameon=True)

fig.tight_layout()
plt.show()

# %%
