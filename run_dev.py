from akowe.akowe import create_app

app = create_app()
app.config['SERVER_NAME'] = 'localhost:5000'

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")