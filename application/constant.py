from application import application
from enum import Enum

db_overwrite_params = {
    'Event': ['title', 'date_start', 'date_end', 'description'],
    'Question': ['question'],
    'Feedback': ['content']
}

urls = {
    'microsoft': {
        'verify_identity': 'https://graph.microsoft.com/v1.0/me/',
        'get_user_events': 'https://graph.microsoft.com/v1.0/me/events'
    }
}

datetime_format = ""

class status(Enum):
    upcoming = 'UPCOMING',
    active = 'ACTIVE'
    finished = 'FINISHED'

class errorMessages(Enum):
    default_error = 'Something went wrong.'

class statusCodes(Enum):
    ok = 200,
    created = 201,
    bad_request = 400,
    unauthorized = 401,
    forbidden = 403,
    not_found = 404,
    method_not_allowed = 405,
    gone = 410,
    im_a_teapot = 418,
    server_error = 500,
    bad_gateway = 502
    

expiration_min = 1e5 #min