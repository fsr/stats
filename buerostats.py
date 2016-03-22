import sqlite3
import time
import json


def get_raw_data():
    '''Fetches all rows from the buerostatus database'''
    connection = sqlite3.connect('buerostatus.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM buerostatus")
    rows = cursor.fetchall()
    connection.close()

    return rows


def init_data():
    '''Initializes a raw data field'''
    data = {}
    for w_day in range(0, 7):
        data[w_day] = {}
        for hour in range(0, 24):
            data[w_day][hour] = {}
            for minute in range(0, 60):
                data[w_day][hour][minute] = []

    return data


def main():
    rows = get_raw_data()

    data = init_data()

    for row in rows:
        date = time.localtime(row[1])
        data[date[6]][date[3]][date[4]].append(row[2])
    with open('results.json', 'w') as f:
        json.dump(data, f, indent=4)


if __name__ == '__main__':
    main()
