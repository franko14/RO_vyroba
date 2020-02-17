import wapi
import plotly.express as px
import plotly.graph_objects as go
import plotly
import warnings
import github3
import datetime
import pandas as pd
import os

plotly_template = plotly.io.templates["plotly_white"]
plotly_template.layout.xaxis.gridcolor = '#a7a7a7'
plotly_template.layout.xaxis.linecolor = '#a7a7a7'
plotly_template.layout.yaxis.gridcolor = '#a7a7a7'
plotly_template.layout.yaxis.linecolor = '#a7a7a7'
plotly_template.layout.yaxis.zerolinecolor = '#a7a7a7'
plotly_template.layout.xaxis.zerolinecolor = '#a7a7a7'
#print (plotly_template.layout)
#exit()


warnings.simplefilter(action='ignore', category=FutureWarning)

config_file_path = 'config.ini'
session = wapi.Session(config_file=config_file_path)

## INPUTS
############################################
# Insert the path to your config file here!
my_config_file = 'config.ini'

# Choose one of the available regions bys using its abbreviation
# as shown on the top of each wattsight page
# (eg https://app.wattsight.com/#tab/power/135/2)
region = 'ro'
#test_images = test_images.reshape((10000,28*28))
#test_images = test_images.astype('float32')/255
# choose one of the four possible categories for this plot:
# 'con' for Consumption
# 'wnd' for Wind Power
# 'spv' for Solar Photovoltaic
# 'rdl' for Residual Load
category = 'wnd'

# Set the aggregation function ['AVERAGE','SUM'] and output frequency of the
# aggregation. The frequency string consists of a letter defining the time unit
# followed by an integer defining the multiple of this unit.
# eg the letter 'H' means "hour", so 'H' or 'H1' defines
# an aggregation frequency of "1 hour", where 'H6' stands for
# "6 hours" and 'H12' for "12 hours". The following letter<->unit
# definitions are valid
# * 'Y': year
# * 'M': month
# * 'W': week
# * 'D': day
# * 'H': hour
# * 'MIN': minutes
# If you want to keep the original 15 minute resolution, set both to None!
freq = 'H'
func = 'AVERAGE'

# get current dates and timeranges to get data
now = pd.Timestamp.now()
today = now.floor('D')
yesterday = today - pd.Timedelta(days=0)
end = today + pd.Timedelta(days=15)

# create the first part of the curve name dependent on the category and region
if category == 'con':
    curve_part1 = 'con ' + region
elif category == 'rdl':
    curve_part1 = 'rdl ' + region
else:
    curve_part1 = 'pro ' + region + ' ' + category

# specifiy timezone based on region
if region == 'tr':
    # Turkey has timezone TRT
    tz = 'trt'
else:
    # All other regions ahve timezone CET
    tz = 'cet'

## get normal data
# get the curve, create curve name based on category, region and timezone
curve_normal = session.get_curve(name=curve_part1+' mwh/h '+tz+' min15 n')
# get data from curve, apply aggregation if defined
normal = curve_normal.get_data(data_from=yesterday, data_to=end,
                               function=func, frequency=freq)
# convert to pandas Series, convert from MWh/h to GWh/h by dividing by 1000
normal = normal.to_pandas(name='Normal')/1000

# get most recent actual data
curve_actual = session.get_curve(name=curve_part1+' mwh/h '+tz+' min15 a')
actual = curve_actual.get_data(data_from=yesterday, function=func,
                               frequency=freq)
# convert to pandas Series, convert from MWh/h to GWh/h by dividing by 1000
actual = actual.to_pandas(name='Actual')/1000

## get backcast for last day
# get the curve, create curve name based on category, region and timezone
curve_actual = session.get_curve(name=curve_part1+' mwh/h '+tz+' min15 s')
# get data from curve, apply aggregation if defined
backcast = curve_actual.get_data(data_from=yesterday, data_to=today,
                                 function=func, frequency=freq)
# convert to pandas Series, convert from MWh/h to GWh/h by dividing by 1000
backcast = backcast.to_pandas(name='Backcast')/1000


# The EC Forecasts are published the following order:
# ... EC00, EC00Ens, EC12, EC12Ens, EC00, EC00Ens, EC12, EC12Ens, ...t
# We want to plot the latest three forecasts, so we first read the latest
# issued version of each forecast together with its issue date

## get EC00 data and issue date
# get the curve, create curve name based on category, region and timezone
curve_EC00 = session.get_curve(name=curve_part1+' ec00 mwh/h '+tz+' min15 f')
# get data for latest issue_date, apply aggregation if defined
EC00 = curve_EC00.get_latest(function=func, frequency=freq)
# get the issue_date if latest issue
EC00_idate = EC00.issue_date
# Convert issue date from UTC to CET make it a string again
EC00_idate = pd.Timestamp(EC00_idate).tz_convert('CET').strftime('%Y-%m-%d')
# Convert TS object to pandas Series, create name based on issue_date
EC00 = EC00.to_pandas(name='EC00 ' + EC00_idate[8:10] + '.' + EC00_idate[5:7])
# only select data from today until 10 days ahead
# convert from MWh/h to GWh/h by dividing by 1000
EC00 = EC00.loc[today:end]/1000

## get EC12 data and issue date
# get the curve, create curve name based on category, region and timezone
curve_EC12 = session.get_curve(name=curve_part1+' ec12 mwh/h '+tz+' min15 f')
# get data for latest issue_date, apply aggregation if defined
EC12 = curve_EC12.get_latest(function=func, frequency=freq)
# get the issue_date if latest issue
EC12_idate = EC12.issue_date
# Convert issue date from UTC to CET make it a string again
EC12_idate = pd.Timestamp(EC12_idate).tz_convert('CET').strftime('%Y-%m-%d')
# Convert TS object to pandas Series, create name based on issue_date
EC12 = EC12.to_pandas(name='EC12 ' + EC12_idate[8:10] + '.' + EC12_idate[5:7])
# only select data from today until 10 days ahead
# convert from MWh/h to GWh/h by dividing by 1000
EC12 = EC12.loc[today:end]/1000

## get EC00Ens data and issue date
# get the curve, create curve name based on category, region and timezone
curve_EC00Ens = session.get_curve(name=curve_part1+' ec00ens mwh/h '+tz+' min15 f')
# get the issue_date if latest issue
EC00Ens_idate = curve_EC00Ens.get_latest(with_data=False).issue_date
# Get list of TS objects for all available tags for latest issue date
# apply aggregation if defined
EC00Ens_tslist = curve_EC00Ens.get_instance(EC00Ens_idate, function=func,
                                            frequency=freq,
                                            tag=curve_EC00Ens.get_tags())
# Convert issue date from UTC to CET make it a string again
EC00Ens_idate = pd.Timestamp(EC00Ens_idate).tz_convert('CET').strftime('%Y-%m-%d')
if EC00Ens_tslist is None:
    # while the EC00ENS forecast is processed, get_latest() function can already
    # return valid values (the average of the ensamble) with an issue date,
    # while the get_instance() function returns None, since not all data
    # is available yet. In this case we set the issue date to "2017-01-01" and
    # ignore the EC00ENS, since then it is the oldest forecast we will not
    # consider further.
    EC00Ens_idate = '2017-01-01'
else:
    # loop through all TS objects (tags)
    # Save them all to a pandas DataFrame, each column is one tag
    for i,ts in enumerate(EC00Ens_tslist):
        if i==0:
            # create the DataFrame
            EC00Ens = ts.to_pandas(name='EC00Ens_'+ts.tag).to_frame()
        else:
            # add columns to the DataFrame
            EC00Ens['EC00Ens_'+ts.tag] = ts.to_pandas()
    # only select data from today until 10 days ahead
    # convert from MWh/h to GWh/h by dividing by 1000
    EC00Ens = EC00Ens.loc[today:end]/1000
    # Save the "Avg" Ensamble data in own variable
    EC00Ens_avg = EC00Ens['EC00Ens_Avg']
    # Add a name based on the issue date
    EC00Ens_avg.name = 'EC00Ens ' + EC00Ens_idate[8:10] + '.' + EC00Ens_idate[5:7]

## get EC12Ens data and issue date
# get the curve, create curve name based on category, region and timezone
curve_EC12Ens = session.get_curve(name=curve_part1+' ec12ens mwh/h '+tz+' min15 f')
# get the issue_date if latest issue
EC12Ens_idate = curve_EC12Ens.get_latest(with_data=False).issue_date
# Get list of TS objects for all available tags for latest issue date
# apply aggregation if defined
EC12Ens_tslist = curve_EC12Ens.get_instance(EC12Ens_idate, function=func,
                                            frequency=freq,
                                            tag=curve_EC12Ens.get_tags())
# Convert issue date from UTC to CET make it a string again
EC12Ens_idate = pd.Timestamp(EC12Ens_idate).tz_convert('CET').strftime('%Y-%m-%d')
if EC12Ens_tslist is None:
    # while the EC12ENS forecast is processed, get_latest() function can already
    # return valid values (the average of the ensamble) with an issue date,
    # while the get_instance() function returns None, since not all data
    # is available yet. In this case we set the issue date to "2017-01-01" and
    # ignore the EC12ENS, since then it is the oldest forecast we will not
    # consider further.
    EC12Ens_idate = '2017-01-01'
else:
    # loop through all TS objects (tags)
    # Save them all to a pandas DataFrame, each column is one tag
    for i,ts in enumerate(EC12Ens_tslist):
        if i==0:
            # create the DataFrame
            EC12Ens = ts.to_pandas(name='EC12Ens_'+ts.tag).to_frame()
        else:
            # add columns to the DataFrame
            EC12Ens['EC12Ens_'+ts.tag] = ts.to_pandas()
    # only select data from today until 10 days ahead
    # convert from MWh/h to GWh/h by dividing by 1000
    EC12Ens = EC12Ens.loc[today:end]/1000
    # Save the "Avg" Ensamble data in own variable
    EC12Ens_avg = EC12Ens['EC12Ens_Avg']
    # Add a name based on the issue date
    EC12Ens_avg.name = 'EC12ENS ' + EC12Ens_idate[8:10] + '.' + EC12Ens_idate[5:7]


##########################################
# find out the time order of the forecasts
##########################################

# which forecast is newer?
if EC00_idate > EC00Ens_idate:
   # EC00 is the latest available forecast!
   last_ens = EC12Ens
   fc_order = [EC12, EC12Ens_avg, EC00]
elif EC00Ens_idate >= EC12_idate:
   # EC00ENS is the latest available forecast!
   last_ens = EC00Ens
   fc_order = [EC12Ens_avg, EC00, EC00Ens_avg]
elif EC12_idate >= EC00Ens_idate:
   # EC12 is the latest available forecast!
   last_ens = EC00Ens
   fc_order = [EC00, EC00Ens_avg, EC12]
else:
   # EC12ENS is the latest available forecast!
   last_ens = EC12Ens
   fc_order = [EC00Ens_avg, EC12, EC12Ens_avg]

normal.name = 'Normal'
#last_ens = last_ens
last_ens.index.name = 'Date'
#print (last_ens.keys())

last_ens['Datestr'] = last_ens.index
last_ens.sort_values(by=['Datestr'])
#print (last_ens)

#print(normal)
#exit(0)
ens_df = last_ens.melt(id_vars=['Datestr']+list(last_ens.columns[0:2]), var_name='ENS_run')
ens_df = ens_df.sort_values(by=['ENS_run', 'Datestr'])

#exit()
ens_df.set_index('Datestr', inplace=True)
#print (df['value'][df['value'] == 'EC00Ens_Avg'])
ens_df = ens_df.sort_values(by=['ENS_run','Datestr'])
ens_df = ens_df.tz_localize(tz=None)

# Create traces
fig = go.Figure()

#fig['layout'].update(height=600, width=600, title='Subplots with Shared X-Axes')
#go.FigureWidget(fig)

fig.add_traces([
                go.Scatter(x=fc_order[0].index, y=fc_order[0].values,
                    mode='lines',
                    line=go.scatter.Line(),
                    line_width=2,
                    line_color='darkred',
                    name=fc_order[0].name
                    ),
                go.Scatter(x=fc_order[1].index, y=fc_order[1].values,
                        mode='lines',
                        line=go.scatter.Line(),
                        line_width=2,
                        line_color='#0008ad',
                        name=fc_order[1].name
                        ),
                go.Scatter(x=fc_order[2].index, y=fc_order[2].values,
                        mode='lines',
                        line=go.scatter.Line(),
                        line_width=3,
                        line_color='red',
                        name=fc_order[2].name
                        ),
                go.Scatter(x=normal.index, y=normal.values,
                        mode='lines',
                        line=go.scatter.Line(),
                        line_width=1,
                        line_color='brown',
                        name='Normal'
                        ),
                go.Box(x=ens_df.index, y=(ens_df['value']),
                                    boxpoints='outliers',
                                    line_width=0.5,
                                    line_color='blue',
                                    opacity=0.5,
                                    name='ENS Spread',
                                    )
                ])

fig.update_layout(title={'text' : 'RO wind forecast',
                        #'y':0.9,
                        'x' : 0.5,
                        'xanchor' : 'center',
                        'font' :  dict(
                                    size=30,
                                    color="#000000"
                                )
                        },
                xaxis_tickformat = '%d.%m.',# %H:00<br>%Y',
                xaxis_rangeslider_visible=True,
                xaxis = dict(
                            #tickmode = 'auto',
                            dtick = 86400000.0,
                            tickfont =  dict(
                                        size=15,
                                        color="#000000"
                                    )
                        ),
                template = "plotly_white",
                legend_orientation = "h",
                #legend_title = "Forecast",
                legend =  dict(y=-0.3),
                shapes=[
                go.layout.Shape(
                                type = 'line',
                                x0 = '2020-02-24 0:00',
                                y0 = 0,
                                x1 = '2020-02-24 0:00',
                                #yref  = 'paper',
                                y1 = 5,
                                line=dict(color = 'darkgreen', width=2),
                                ),
                go.layout.Shape(
                                type = 'line',
                                x0 = '2020-03-02 0:00',
                                y0 = 0,
                                x1 = '2020-03-02 0:00',
                                #yref  = 'paper',
                                y1 = 5,
                                line=dict(color = 'darkgreen', width=2),
                                )]
                )


fig.update_xaxes(showgrid=True, zeroline=True)
fig.update_yaxes(range=[0,5],showgrid=True, zeroline=True)
#fig.update_xaxes(showgrid=True, gridwidth=1)

import plotly.io as pio
pio.write_html(fig, file='index.html', auto_open=False)

from git import Repo

today_date = datetime.datetime.now().strftime('%d.%-m.%Y')
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
PATH_OF_GIT_REPO = fr'{dname}/.git'  # make sure .git folder is properly configured
COMMIT_MESSAGE = f'{today_date} update'

def git_push():
    try:
        repo = Repo(PATH_OF_GIT_REPO)
        repo.git.add(update=True)
        repo.index.commit(COMMIT_MESSAGE)
        origin = repo.remote(name='origin')
        origin.push()
    except:
        print('Some error occured while pushing the code')

git_push()
