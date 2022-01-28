import sqlite3

results_cons = {}

def init_users():
    with sqlite3.connect('users.db') as users_con:
        users_con.execute("""
            CREATE TABLE IF NOT EXISTS USERS (
                handle TEXT PRIMARY KEY,
                targeturl TEXT
            )
        """)

def clear_users():
    with sqlite3.connect('users.db') as users_con:
        users_con.execute('DELETE FROM USERS')

def user_exists(handle):
    with sqlite3.connect('users.db') as users_con:
        user_exists_result = users_con.execute('SELECT EXISTS(SELECT 1 FROM USERS WHERE handle = ?)', (handle,))
        result = user_exists_result.fetchall()
        return result[0][0] == 1

def get_userURL(handle):
    with sqlite3.connect('users.db') as users_con:
        user_target_url = users_con.execute('SELECT targeturl FROM USERS WHERE handle = ?', (handle,))
        result = user_target_url.fetchall()
        return result[0][0]

def add_userURL(handle, url):
    with sqlite3.connect('users.db') as users_con:
        users_con.execute('INSERT INTO USERS (handle, targeturl) values(?, ?)', (handle, url))

def init_user_results(handle):
    with sqlite3.connect('users.db') as users_con:
        query = '''
            CREATE TABLE IF NOT EXISTS {0} (
                url TEXT PRIMARY KEY,
                img_url TEXT,
                title TEXT,
                epoch int,
                price TEXT,
                distance TEXT
            )
        '''.format(handle)
        users_con.execute(query)

def delete_user_results(handle):
    with sqlite3.connect('users.db') as users_con:
        query = '''
            DELETE FROM {0}
        '''.format(handle)
        users_con.execute(query)

def print_user_results(handle):
    with sqlite3.connect('users.db') as users_con:
        query = '''
            SELECT * FROM {0}
        '''.format(handle)
        user_results = users_con.execute(query).fetchall()
        print(user_results)

def datetime_to_epoch(datetime):
    print(datetime)
    return int(datetime.strftime('%s')) * 1000

def add_user_result(handle, result):
    with sqlite3.connect('users.db') as users_con:
        epoch_time = datetime_to_epoch(result.datetime)
        query = '''
            INSERT INTO {0} VALUES(?, ?, ?, ?, ?, ?)
        '''.format(
            handle
        )
        users_con.execute(query, (result.url, result.img_url, result.title,
            epoch_time, result.price, result.distance))

def update_userURL(handle, url):
    with sqlite3.connect('users.db') as users_con:
        users_con.execute('UPDATE USERS SET targeturl = ? WHERE handle = ?', (url, handle))

def get_users():
    with sqlite3.connect('users.db') as users_con:
        user_target_url = users_con.execute('SELECT * FROM USERS')
        result = user_target_url.fetchall()
        return result
