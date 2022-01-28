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

def update_userURL(handle, url):
    with sqlite3.connect('users.db') as users_con:
        users_con.execute('UPDATE USERS SET targeturl = ? WHERE handle = ?', (url, handle))

def get_users():
    with sqlite3.connect('users.db') as users_con:
        user_target_url = users_con.execute('SELECT * FROM USERS')
        result = user_target_url.fetchall()
        return result
