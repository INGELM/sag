from app import create_app
from flask import redirect, flash
from app.extensions import db

app = create_app()


@app.route('/')
def index():
    
    return redirect('/login')




if __name__ == '__main__':
    app.run(debug=False)

