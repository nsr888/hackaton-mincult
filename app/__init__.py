from flask import Flask, g, render_template, request
from dateutil.parser import parse as duparse
# from dateutil import tz
import sqlite3
import locale

app = Flask(__name__)


@app.route('/')
def index():
    con = connect_db()
    con.row_factory = dict_factory
    cursor = con.cursor()
    cur = cursor.execute('''
        select
            *
        from DWH_DIM_EVENTS_HIST
        order by start_dt
        limit 9
    ''')
    events = [dict(row) for row in cur.fetchall()]
    con.close()
    return render_template('index.html', events=events)


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'GET':
        key = request.args.get('key', '')
        con = connect_db()
        con.row_factory = dict_factory
        cursor = con.cursor()
        var1 = '%' + key + '%'
        cur = cursor.execute('''
            select
                *
            from DWH_DIM_EVENTS_HIST
            where name like ? or description like ? or short_description like ?
            order by start_dt
            limit 9
        ''', [var1, var1, var1])
        events = [dict(row) for row in cur.fetchall()]
        con.close()
        return render_template('index.html', events=events)
    return '''Not found'''


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


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect_db():
    return sqlite3.connect('app.db')


def main():
    app.run(debug=True)


if __name__ == '__main__':
    main()
