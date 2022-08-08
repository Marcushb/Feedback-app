from application import application
from flask import request, jsonify

@application.errorhandler(404)
def not_found(e):
    return jsonify({
        'errorMessage': f'{e}',
        'route': f'{request.url}',
        'statusCode': 404
    })

@application.errorhandler(405)
def not_found(e):
    return jsonify({
        'errorMessage': f'{e}',
        'statusCode': 405
    })

@application.errorhandler(500)
def server_error(e):
    return jsonify({
        'errorMessage': f'{e}',
        'statusCode': 500
    })