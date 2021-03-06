import pandas
import zipfile
import argparse
import os
#import matplotlib.pyplot as plt
#import matplotlib
import bokeh
from bokeh.charts import color
from bokeh.plotting import show
from bokeh.layouts import column


bokeh.charts.defaults.width = 1200
bokeh.charts.defaults.legend = False

parser = argparse.ArgumentParser(description="Process PG\&E Data")
parser.add_argument('zipfile')
parser.add_argument('--temps', dest='tfile', help='NWS temperature record')

args = parser.parse_args()

if os.getenv('temp') is None:
    print("Can't extract zip file - no temp directory defined!")
    exit()

tempdir = os.getenv('temp') + '\\'

gasfile = ''
elecfile = ''
tfile = args.tfile


with zipfile.ZipFile(args.zipfile, 'r') as myzip:
    zi = myzip.infolist()
    for f in zi:
        # print (f.filename)
        if 'gas' in f.filename:
            gasfile = f.filename
        elif 'elec' in f.filename:
            elecfile = f.filename
    myzip.extractall(path=tempdir)


def truncRes(df):
    daily = df
    daily = df.resample("1D").sum()  # Make sure the dataframe is really daily frequency
    daily['Current Year (lagged)'] = daily['USAGE'].shift(-365, freq="D")
    truncated_df = daily[:daily.index.max() - pandas.to_timedelta('365 days')]  # Only interested in last two years
    renamed = truncated_df.rename(columns={'USAGE': 'Prior Year'})
    resampled = renamed.resample("1W").sum()
    return resampled

if tfile is not None:
    tdf = pandas.read_csv(tfile, index_col=2, parse_dates=True)
    tdf['Current Year TMIN (lagged)'] = tdf['TMIN'].shift(-365, freq="D")
    trunctdf = tdf[:tdf.index.max() - pandas.to_timedelta('365 days')]
    trunctdf = trunctdf.resample("1W").mean()


if gasfile != '':
    gasdf = pandas.read_csv(tempdir+gasfile, skiprows=5, index_col=1, parse_dates=True)
    gastochart = truncRes(gasdf)
    try:
        trunctdf
    except:
        pass
    else:
        gastochart['TMIN'] = trunctdf['TMIN']
        gastochart['Current Year TMIN (lagged)'] = trunctdf['Current Year TMIN (lagged)']
    gaschart = bokeh.charts.TimeSeries(gastochart, title="Gas Usage",  xlabel="Date", legend=True,ylabel="Therms")

if elecfile != '':
    elecdf = pandas.read_csv(tempdir+elecfile, skiprows=5, index_col=1, parse_dates=True)
    electochart = truncRes(elecdf)
    elecchart = bokeh.charts.TimeSeries(electochart, title="Electricity Usage", legend=True, xlabel="Date", ylabel="kWh")


show(column(gaschart, elecchart))
