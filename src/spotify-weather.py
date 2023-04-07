from flask import Flask, render_template, request
from weather import main as get_weather

app = Flask("411-Group-Project")

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()