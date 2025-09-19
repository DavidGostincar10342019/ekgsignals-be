from . import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False, port=8000)  # Debug OFF za brzinu
