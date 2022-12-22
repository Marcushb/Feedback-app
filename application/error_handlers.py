from application import application
from flask import request, jsonify

@application.errorhandler(404)
def not_found(e):
    return jsonify({
        'errorMessage': 'Not found.',
        'devInfo': f'{e}',
        'route': f'{request.url}',
        'statusCode': 404
    }), 404

@application.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        'errorMessage': "Not allowed.",
        'devInfo': f'{e}',
        'route': f'{request.url}',
        'statusCode': 405
    }), 405

@application.errorhandler(500)
def server_error(e):
    return jsonify({
        'errorMessage': "Server error.",
        'devInfo': f'{e}',
        'route': f'{request.url}',
        'statusCode': 500
    }), 500