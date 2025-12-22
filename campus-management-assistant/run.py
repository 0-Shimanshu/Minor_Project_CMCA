from app import create_app

app = create_app()

if __name__ == "__main__":
    # Built-in Flask dev server; no routes yet
    app.run()
