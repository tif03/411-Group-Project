from flask import Flask, render_template, jsonify
import weather

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather')
def get_weather():
    city, country_code, description, fehTemperature, celTemperature = weather.find_long_lat()
    return jsonify(city=city, country_code=country_code, description=description, fehTemperature=fehTemperature, celTemperature=celTemperature)

if __name__ == '__main__':
    app.run(debug=True)