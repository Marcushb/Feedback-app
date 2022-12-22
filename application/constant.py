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

expiration_min = 1e5 #min