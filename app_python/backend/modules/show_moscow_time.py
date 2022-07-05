from flask import Blueprint, render_template
import datetime


show_moscow_time_bp = Blueprint('show_moscow_time', __name__)


@show_moscow_time_bp.route('/', methods=['GET'])
def show_moscow_time():
    offset = datetime.timezone(datetime.timedelta(hours=3))
    time = datetime.datetime.now(offset)
    with open('logs/visits.log', 'a') as fp:
        fp.write(time.strftime("%m/%d/%Y, %H:%M:%S"))
        fp.write('\n')
    return render_template('index.html')


@show_moscow_time_bp.route('/visits', methods=['GET'])
def show_visits():
    with open('logs/visits.log', 'r') as fp:
        return fp.read()
