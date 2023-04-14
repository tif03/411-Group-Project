from flask import Flask, render_template, request
from weather import main as get_weather

app = Flask("411-Group-Project")

# we need to pass in what methods are allowed to be called from this route, by default only get is allowed
@app.route("/", methods=['GET', 'POST'])
def home():
    #initialize data to none so even if its a get method render template can still have something declared for data
    data = None
    
    # when the user clicks the button to send in the form, they make a post request
    if request.method == 'POST':
        city = request.form['cityName']
        state = request.form['stateName']
        country = request.form['countryName']
        
        # we will call our get_weather method we created, save result in data
        data = get_weather(city, state, country)
    
    # we then pass in data as a parameter to the front end so we can display it there
    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run()