from application.models import User, Event, Question, Feedback
from flask import request, jsonify
import flask
from application.constant import db_overwrite_params, status, errorMessages
from application import db
from datetime import datetime, timedelta
from typing import Union

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

def setIsActive(event, time_delta):
    startDate = datetime.strptime(event.date_start, "%Y-%m-%dT%H:%M:%SZ")
    endDate = datetime.strptime(event.date_end, "%Y-%m-%dT%H:%M:%SZ")
    cap_time = endDate + timedelta(minutes = time_delta)
    
    if event.isActive == status.upcoming.value and (datetime.utcnow() >= startDate): 
        event.isActive = status.active.value
        db.session.commit()
        
        return event.isActive

    # elif event.isActive == 'ACTIVE' and (datetime.utcnow() < cap_time):
    #     return event.isActive

    elif event.isActive == status.active.value and (datetime.utcnow() > cap_time): 
        event.isActive = status.finished.value
        # pin_delete = Pin.query.filter_by(pin = event.pin).delete()
        db.session.commit()

        return event.isActive

    return event.isActive

def none_json(param_name: str) -> flask.Response:
    return jsonify({
        "errorMessage": errorMessages.default_error.value,
        "devInfo": f"Parameter '{param_name}' is None",
        "route": f"{request.url}",
        "statusCode": 404
    }), 404

def db_query_filter(
    table: str, 
    table_key: Union[str, int], 
    input_key: Union[str, int],
    type: str,
    param_name: str
    ):
    data = eval(f"{table}.query.filter_by({table_key} = {input_key}).{type}()")
    if data is None:
        return none_json(param_name)
    return data

def force_isActive(event):
    event.isActive = status.active.value
    db.session.commit()

def json_response(
    errorMessage: str,
    devInfo: str, 
    route: str, 
    statusCode: str = None
    ) -> flask.Response:

    return jsonify({
        "errorMessage": errorMessage,
        "devInfo": devInfo,
        "route": route,
        "statusCode": statusCode
    })

def create_feedback_summary(feedback_data: list) -> dict:
    feedback_rating = [feedback.rating for feedback in feedback_data]
    if len(feedback_rating) == 0:
        return None
    else:
        feedback_object = {}
        feedback_object['rating1'] = feedback_rating.count(1)
        feedback_object['rating2'] = feedback_rating.count(2)
        feedback_object['rating3'] = feedback_rating.count(3)
        feedback_object['rating4'] = feedback_rating.count(4)
        feedback_object['feedbackCount'] = len(feedback_rating)
    return feedback_object