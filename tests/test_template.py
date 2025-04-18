from flask import render_template
from akowe.akowe import create_app

app = create_app()

with app.app_context():
    try:
        render_template('dashboard/index.html')
        print('Successfully rendered template!')
    except Exception as e:
        print(f'Error: {str(e)}')