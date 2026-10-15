# Libraries needed (pandas is not standard and must be installed in Python)
'''import requests
import pandas as pd
import matplotlib.pyplot as plt
 
# Insert your own client ID here
client_id = 'a47f0003-8842-458d-b3cb-f14545ecfdb8'
 
# Define endpoint and parameters
endpoint = 'https://frost.met.no/observations/v0.jsonld'
parameters = {
'sources': 'SN17850',
'elements': 'mean(air_temperature P1D)',
'referencetime': '2025-01-01/2025-12-31',
}
 
# Issue an HTTP GET request
r = requests.get(endpoint, parameters, auth=(client_id,''))
# Extract JSON data
json = r.json()
 
# Check if the request worked, print out any errors
if r.status_code == 200:
    data = json['data']
    print('Data retrieved from frost.met.no!')
else:
    print('Error! Returned status code %s' % r.status_code)
    print('Message: %s' % json['error']['message'])
    print('Reason: %s' % json['error']['reason'])
 
# This will return a Dataframe with all of the observations in a table format
'''
df = pd.DataFrame()
for i in range(len(data)):
    row = pd.DataFrame(data[i]['observations'])
    row['referenceTime'] = data[i]['referenceTime']
    row['sourceId'] = data[i]['sourceId']
    df = df.append(row)
 
df = df.reset_index()
 
df.head()
'''

# Ny pandas
rows = []
for i in range(len(data)):
    row = pd.DataFrame(data[i]['observations'])
    row['referenceTime'] = data[i]['referenceTime']
    row['sourceId'] = data[i]['sourceId']
    rows.append(row)  # Legger til i den vanlige Python-listen

# Slår sammen alle DataFrames i listen til én stor DataFrame
df = pd.concat(rows, ignore_index=True)

df.head()
df.tail()

import matplotlib.pyplot as plt

# Konverter tid til ekte datetime-objekter hvis du ikke har gjort det
df['referenceTime'] = pd.to_datetime(df['referenceTime'])

# Plot linje (f.eks. tid på X-aksen og verdi på Y-aksen)
df.plot(x='referenceTime', y='value', kind='line', figsize=(10, 5))

plt.title('Tidsrekke for observasjoner')
plt.xlabel('Tid')
plt.ylabel('Verdi')
plt.grid(True)
plt.show()

'''

# Libraries needed (pandas is not standard and must be installed in Python)
import requests
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
 
# Insert your own client ID here
client_id = ''
 
# Define endpoint and parameters
endpoint = 'https://frost.met.no/observations/v0.jsonld'
parameters = {
'sources': 'SN17850',
'elements': 'mean(air_temperature P1D)',
'referencetime': '2025-01-01/2025-12-31',
}
 
# Issue an HTTP GET request
r = requests.get(endpoint, parameters, auth=(client_id,''))
# Extract JSON data
json = r.json()
 
# Check if the request worked, print out any errors
if r.status_code == 200:
    data = json['data']
    print('Data retrieved from frost.met.no!')
else:
    print('Error! Returned status code %s' % r.status_code)
    print('Message: %s' % json['error']['message'])
    print('Reason: %s' % json['error']['reason'])
    raise SystemExit(1)  # stopp her, ellers finnes ikke `data`
 
# Build one table for all the data
rows = []
for item in data:
    row = pd.DataFrame(item['observations'])
    row['referenceTime'] = item['referenceTime']
    row['sourceId'] = item['sourceId']
    rows.append(row)
 
df = pd.concat(rows, ignore_index=True)
print(df.head())
 
# --- Cleans the data ---
df['referenceTime'] = pd.to_datetime(df['referenceTime'])
# Frost gives two values per day: PT0H (kl. 00-00) og PT6H (kl. 06-06).
# Only keep one or the table gets twice as long.
df = df[df['timeOffset'] == 'PT0H']
print(f'{len(df)} dager med data')
 
# --- Plot ---
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df['referenceTime'], df['value'], color='tab:red', linewidth=1.2)
ax.axhline(0, color='grey', linewidth=0.8, linestyle='--')  
ax.set_title('Daily mean air temperature, Ås (SN17850), 2025')
ax.set_xlabel('Date')
ax.set_ylabel('Temperature (°C)')
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.grid(alpha=0.3)
fig.tight_layout()
plt.show()
 
# --- Summary table ---
summary = df['value'].agg(['mean', 'median', 'min', 'max']).round(1)
summary.index = ['Mean', 'Median', 'Min', 'Max']
summary = summary.to_frame(name='Temperature (°C)')
print('\nAir temperature summary, Ås 2025')
print(summary)

