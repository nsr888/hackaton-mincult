from flask import Flask, g, render_template, request, session
from dateutil.parser import parse as duparse
# from dateutil import tz
import sqlite3
import locale
import json

app = Flask(__name__)
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'Qi5GYovFnfNhZaigQWdckhJP'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True


@app.route('/')
def today():
    likes_list = get_likes_list()
    con = connect_db()
    con.row_factory = dict_factory
    cursor = con.cursor()
    cur = cursor.execute('''
        select
            *
        from DWH_DIM_EVENTS_HIST
        where date(start_dt) = date('now')
        order by start_dt
        limit 96
    ''')
    events = [dict(row) for row in cur.fetchall()]
    cur = cursor.execute('''
        select
            *
        from DWH_FACT_CATEGORIES
    ''')
    categories = [dict(row) for row in cur.fetchall()]
    con.close()
    return render_template('index.html', events=events, categories=categories,
            active="today", likes_list=likes_list)


@app.route('/tomorrow/')
def tomorrow():
    likes_list = get_likes_list()
    con = connect_db()
    con.row_factory = dict_factory
    cursor = con.cursor()
    cur = cursor.execute('''
        select
            *
        from DWH_DIM_EVENTS_HIST
        where date(start_dt) = date('now', '+1 day')
        order by start_dt
        limit 96
    ''')
    events = [dict(row) for row in cur.fetchall()]
    cur = cursor.execute('''
        select
            *
        from DWH_FACT_CATEGORIES
    ''')
    categories = [dict(row) for row in cur.fetchall()]
    con.close()
    return render_template('index.html', events=events, categories=categories,
            active="tomorrow", likes_list=likes_list)


@app.route('/free/')
def free():
    likes_list = get_likes_list()
    con = connect_db()
    con.row_factory = dict_factory
    cursor = con.cursor()
    cur = cursor.execute('''
        select
            *
        from DWH_DIM_EVENTS_HIST
        where is_free = True 
        and date(start_dt) >= date('now')
        order by start_dt
        limit 96
    ''')
    events = [dict(row) for row in cur.fetchall()]
    cur = cursor.execute('''
        select
            *
        from DWH_FACT_CATEGORIES
    ''')
    categories = [dict(row) for row in cur.fetchall()]
    con.close()
    return render_template('index.html', events=events, categories=categories,
            active="free", likes_list=likes_list)


@app.route('/7days/')
def seven_days():
    likes_list = get_likes_list()
    con = connect_db()
    con.row_factory = dict_factory
    cursor = con.cursor()
    cur = cursor.execute('''
        select
            *
        from DWH_DIM_EVENTS_HIST
        where date(start_dt) >= date('now')
        and date(start_dt) <= date('now', '+7 day')
        order by start_dt
        limit 96
    ''')
    events = [dict(row) for row in cur.fetchall()]
    cur = cursor.execute('''
        select
            *
        from DWH_FACT_CATEGORIES
    ''')
    categories = [dict(row) for row in cur.fetchall()]
    con.close()
    return render_template('index.html', events=events, categories=categories,
            active="7days", likes_list=likes_list)


@app.route('/cat/<cat>/')
def categories(cat):
    likes_list = get_likes_list()
    con = connect_db()
    con.row_factory = dict_factory
    cursor = con.cursor()
    cur = cursor.execute('''
        select
            *
        from DWH_DIM_EVENTS_HIST
        where category_sysname = ?
        and date(start_dt) >= date('now')
        order by start_dt
        limit 96
    ''', [cat])
    events = [dict(row) for row in cur.fetchall()]
    cur = cursor.execute('''
        select
            *
        from DWH_FACT_CATEGORIES
    ''')
    categories = [dict(row) for row in cur.fetchall()]
    con.close()
    return render_template('index.html', events=events, categories=categories,
            active=cat, likes_list=likes_list)


@app.route('/search', methods=['POST', 'GET'])
def search():
    likes_list = get_likes_list()
    if request.method == 'GET':
        key = request.args.get('key', '')
        con = connect_db()
        con.row_factory = dict_factory
        cursor = con.cursor()
        var1 = '%' + key[:-1] + '%'
        cur = cursor.execute('''
            select
                *
            from DWH_DIM_EVENTS_HIST
            where
                (name like ?
                or description like ?
                or short_description like ?)
                and date(start_dt) >= date('now')
            order by start_dt
            limit 9
        ''', [var1, var1, var1])
        events = [dict(row) for row in cur.fetchall()]
        cur = cursor.execute('''
            select
                *
            from DWH_FACT_CATEGORIES
        ''')
        categories = [dict(row) for row in cur.fetchall()]
        con.close()
        return render_template('index.html', events=events,
                categories=categories, active="main", likes_list=likes_list)
    return '''Not found'''


@app.route('/like', methods=['GET', 'POST'])
def like():
    # data = request.get_json(force=True)
    data = request.get_json()
    like_id = int(data['like_id'])
    likes_list = []
    if 'likes_list' not in session:
        session['likes_list'] = []
    likes_list = session['likes_list']
    if like_id not in likes_list:
        likes_list.append(like_id)
        session['likes_list'] = likes_list
    print(session)
    return ('', 204)


@app.route('/show_liked/', methods=['GET', 'POST'])
def show_liked():
    likes_list = get_likes_list()
    if request.method == 'GET':
        key = request.args.get('clear', '')
        if key == 'all':
            session['likes_list'] = []
        elif key != '':
            likes_list = session['likes_list']
            if int(key) in likes_list:
                likes_list.remove(int(key))
                session['likes_list'] = likes_list
        likes_list = session['likes_list']
    # print(likes_list)
    con = connect_db()
    con.row_factory = dict_factory
    cursor = con.cursor()
    cur = cursor.execute('''
        select
            *
        from DWH_DIM_EVENTS_HIST
        where id in ({seq})
        order by start_dt
    '''.format(seq=','.join(['?']*len(likes_list))), likes_list)
    events = [dict(row) for row in cur.fetchall()]
    cur = cursor.execute('''
        select
            *
        from DWH_FACT_CATEGORIES
    ''')
    categories = [dict(row) for row in cur.fetchall()]
    con.close()
    return render_template('index.html', events=events, categories=categories,
            active="show_liked", likes_list=likes_list)


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return '''404 error'''


@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    locale.setlocale(locale.LC_TIME, "ru_RU")
    date = duparse(date)
    # MOS = tz.gettz('Europe / Moscow')
    native = date.replace(tzinfo=None)
    format ='%a, %d %b %Y %H:%M'
    return native.strftime(format)


@app.template_filter("is_in_list")
def is_any(search=0, list=None):
    # print(search)
    # print(list)
    if search in list:
        return True
    return False


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect_db():
    return sqlite3.connect('app.db')


def get_likes_list():
    if 'likes_list' not in session:
        session['likes_list'] = []
    return session['likes_list']



def main():
    app.run(debug=True)


if __name__ == '__main__':
    main()
