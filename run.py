from app import create_app
from flask import redirect, flash
from app.extensions import socketio 


app = create_app()


@app.route('/')
def index():
    
    return redirect('/login')




if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

