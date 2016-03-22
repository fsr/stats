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

    avg_data = {
        day_k: {
            hour_k: {
                min_k: sum(min_v)/len(min_v)
                for min_k, min_v in hour_v.items()
            }
            for hour_k, hour_v in day_v.items()
        }
        for day_k, day_v in data.items()
    }

    with open('results.json', 'w') as f:
        json.dump(avg_data, f, indent=4)

    all_x = []
    cnt = 0
    for day in avg_data:
        for hour in avg_data[day]:
            for minute in avg_data[day][hour]:
                all_x.append(avg_data[day][hour][minute])

    import matplotlib.pyplot as plt
    plt.plot(all_x)
    plt.ylabel('Lichtsensor Output')
    plt.xlabel('Zeit')
    plt.axis([0, 10080, 0, 1000])
    plt.savefig('test.png')
    plt.show()


if __name__ == '__main__':
    main()
