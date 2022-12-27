from application import application
from application import ngrok

if ngrok:
    if __name__ == '__main__':
        application.run()
else:
    if __name__ == '__main__':
        application.run(debug  =True)
# if __name__ == '__main__':
#     application.run(debug = True, host="0.0.0.0")

    # application.run(debug = True)