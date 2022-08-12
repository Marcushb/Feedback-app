from application import application

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