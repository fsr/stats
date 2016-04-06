import sqlite3
import time
import json
import csv
import sys
import os
import requests
from punchcard.punchcard import punchcard

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
TEMP_DB = SCRIPT_PATH + '/data.db'
STATS_DB = 'https://ifsr.de/buerostatus/buerostatus.db'
THRESHOLD = 300.0  # light values below the threshold will be ignored


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


def init_data():
    '''Initializes a raw data field which is going to be populated with
    data from the database'''
    data = {}
    for w_day in range(0, 7):
        data[w_day] = {}
        for hour in range(0, 24):
            data[w_day][hour] = {}
            for minute in range(0, 60):
                data[w_day][hour][minute] = []

    return data


def main(args):
    if len(args) < 2:
        IMGPATH = SCRIPT_PATH + '/punchcard.png'
    else:
        IMGPATH = args[1]

    # days and hours for the punchcard labels
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday']
    hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
             16, 17, 18, 19, 20, 21, 22, 23]

    # get raw data, initialize the data field and populate the 'data' structure
    rows = get_raw_data()
    data = init_data()

    print('Calculating the average light intensity per hour... ')

    for row in rows:
        date = time.localtime(row[1])
        # filter out every light value below the threshold (e.g. sunlight)
        if row[2] >= THRESHOLD:
            data[date[6]][date[3]][date[4]].append(row[2])
        else:
            data[date[6]][date[3]][date[4]].append(0)

    # calculate the average per hour light levels
    avg_per_m_data = {
        day_k: {
            hour_k: {
                min_k: sum(min_v) / len(min_v)
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
    for day_id in avg_per_h_data:
        vals = []
        for i in range(0, 24):
            vals.append(avg_per_h_data[day_id][i])
        plot_data.append(vals)

    print('DONE!')

    # generate the punchcard
    punchcard(IMGPATH, plot_data, days, hours)
    print('Job finished. You can find the image at {}'.format(IMGPATH))


if __name__ == '__main__':
    args = sys.argv
    main(args)
