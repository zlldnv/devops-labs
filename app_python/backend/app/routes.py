from modules.show_moscow_time import show_moscow_time_bp


def route(app):
    app.register_blueprint(show_moscow_time_bp)
