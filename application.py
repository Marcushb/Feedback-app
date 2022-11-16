from application import application
from application import ngrok

# if __name__ == '__main__':
#     application.run()
if __name__ == '__main__':
    application.run(debug = True, host="0.0.0.0")

    # application.run(debug = True)