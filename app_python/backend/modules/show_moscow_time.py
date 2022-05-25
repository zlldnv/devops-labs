from flask import Blueprint, render_template
import datetime


show_moscow_time_bp = Blueprint('show_moscow_time', __name__)


@show_moscow_time_bp.route('/', methods=['GET'])
def show_moscow_time():
    offset = datetime.timezone(datetime.timedelta(hours=3))
    return render_template('index.html')
