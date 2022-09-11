from application.models import Event
from flask import request
from application.constant import db_overwrite_params
from application import db

def change_event(app_id):
    event = Event.query.filter_by(app_id = app_id)
    vals = [request.get_json(f'{var}') for var in db_overwrite_params['Event']]
    event_title = vals[db_overwrite_params['Event'] == 'title']
    event_date_start = vals[db_overwrite_params['Event'] == 'date_start']
    event_date_end = vals[db_overwrite_params['Event'] == 'date_start']
    event_description = vals[db_overwrite_params['Event'] == 'description']

    for var in db_overwrite_params['Event']:
        var_change = "_".join(["event", var])
        if f'{var_change}' == None:
            continue

        match var_change:
            case 'title':
                event.title = event_title
            case 'date_start':
                event.date_start = event_date_start
            case 'date_end':
                event.date_end = event_date_end
            case 'description':
                event.description = event_description
    db.session.commit()