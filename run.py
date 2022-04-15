from app import app
from app import ngrok

if ngrok:
    if __name__ == '__main__':
        app.run()
else:
    if __name__ == '__main__':
        app.run(debug = True)