import sqlite3
import time
import sys
import os
import requests
from punchcard.punchcard import punchcard

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
TEMP_DB = SCRIPT_PATH + '/data.db'
DEFAULT_FILENAME = SCRIPT_PATH + '/punchcard.png'
STATS_DB = 'https://ifsr.de/buerostatus/buerostatus.db'
THRESHOLD = 300.0  # light values below the threshold will be ignored
DEFAULT_BINSIZE = 60 # minutes per column, must be factor of 60


def download_db():
    '''Downloads the latest version of the 'buerostatus' database'''
    print('Getting the latest database data... ')
    with open(TEMP_DB, 'w') as f:
        r = requests.get(STATS_DB)
        f.write(r.content)
    print('DONE!')


def get_raw_data():
    '''Downloads the database & fetches all rows, which are returned as list'''
    download_db()
    connection = sqlite3.connect(TEMP_DB)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM buerostatus")  # ORDER BY ts?
    rows = cursor.fetchall()
    connection.close()

    return rows


def init_data(binsize):
    '''Initializes a raw data field which is going to be populated with
    data from the database'''
    data = {}
    for w_day in range(0, 7):
        data[w_day] = {}
        for hour in range(0, 24):
            data[w_day][hour] = {}
            for minute in range(0, 60/binsize):
                data[w_day][hour][minute] = []

    return data

def bin_by_minutes(value, minutes):
    return int(value/minutes)

def main(args):
    if len(args) < 2:
        IMGPATH = DEFAULT_FILENAME
        BINSIZE = DEFAULT_BINSIZE
    elif len(args) < 3:
        # both argument are optional - check if only argument is a number
        if(args[1].isdigit()):
            IMGPATH = DEFAULT_FILENAME
            BINSIZE = int(args[1])
        else:
            IMGPATH = args[1]
            BINSIZE = DEFAULT_BINSIZE
    else:
        # handle switched arguments
        if(args[1].isdigit() and not args[2].isdigit()):
            IMGPATH = args[2]
            BINSIZE = int(args[1])
        else:
            IMGPATH = args[1]
            BINSIZE = int(args[2])

    if(60 % BINSIZE != 0):
        print('Bin size must be factor of 60.')
        quit()
    if(BINSIZE < 2):
        print('Output file would be too large, setting minimum bin size of 2 minutes.')
        BINSIZE = 2

    # days and hours:minutes for the punchcard labels
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday']
    bins = []
    for h in range(0,24):
        for q in range(0, 60/BINSIZE):
            # format time
            bins.append(str(h).zfill(2)+':'+str(q*BINSIZE).zfill(2))

    # get raw data, initialize the data field and populate the 'data' structure
    rows = get_raw_data()
    data = init_data(BINSIZE)

    print('Calculating the average light intensity per {} minutes... '.format(BINSIZE))

    for row in rows:
        date = time.localtime(row[1])
        # filter out every light value below the threshold (e.g. sunlight)
        if row[2] >= THRESHOLD:
            data[date[6]][date[3]][bin_by_minutes(date[4], BINSIZE)].append(row[2])

        else:
            data[date[6]][date[3]][bin_by_minutes(date[4], BINSIZE)].append(0)

    # calculate the average per hour light levels
    avg_per_m_data = {
        day_k: {
            hour_k: {
                min_k: (sum(min_v) / len(min_v)) if len(min_v)>0 else 0
                for min_k, min_v in hour_v.items()
            }
            for hour_k, hour_v in day_v.items()
        }
        for day_k, day_v in data.items()
    }

    avg_per_h_data = {
        day_k: {
            hour_k: round(sum(hour_v.values()) / len(hour_v.values()))
            for hour_k, hour_v in day_v.items()
        }
        for day_k, day_v in avg_per_m_data.items()
    }

    # fill the stats in the plot-data list
    plot_data = []
    for day_id in avg_per_m_data:
        vals = []
        for i in range(0, 24):
            for j in range(0, 60/BINSIZE):
                vals.append(avg_per_m_data[day_id][i][j])
        plot_data.append(vals)

    print('DONE!')

    # generate the punchcard
    punchcard(IMGPATH, plot_data, days, bins)
    print('Job finished. You can find the image at {}'.format(IMGPATH))


if __name__ == '__main__':
    args = sys.argv
    main(args)
