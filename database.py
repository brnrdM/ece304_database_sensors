from flask import Flask, request, render_template
import requests
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from dataclasses import dataclass
import pandas as pd
from pandas.io.formats.style import Styler

@dataclass
class Sensor_Values_inClass:
    id: str
    name: str
    location_dht: str
    temperature: float
    humidity: float

@dataclass
class Sensor_Values_inLab:
    name_tcs: str
    id_tcs: int
    location_tcs: str
    red: float
    green: float
    blue: float
    clr_temp: float
    lux: float
    name_bme: str
    id_bme: int
    location_bme: str
    temperature: float
    pressure: float
    altitude: float 
    humidity: float

dic_circuits = {}

# class Circuit():
#     def __init__(self, cid, name, ip="0.0.0.0"):
#         self.cid = cid
#         self.name = name
#         self.ip = ip
#     def update_ip(self,new_ip):
#         self.ip = new_ip
#     def get_ip(self):
#         return "http://" + self.ip

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///test_database.db'

db = SQLAlchemy(app)


class Sensor(db.Model):
    # Parent
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    # https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html
    posts_dht = db.relationship('Post_DHT', backref='author', lazy=True)
    posts_bme = db.relationship('Post_BME', backref='author', lazy=True)
    posts_tcs = db.relationship('Post_TCS', backref='author', lazy=True)

    def __repr__(self):
        return f"Sensor('{self.id}', '{self.name}', '{self.location}')"

class Post_DHT(db.Model):
    __tablename__ = 'post_DHT'
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now())
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)

    def __repr__(self):
        return f"Sensor('{self.date_posted}', '{self.temperature}', '{self.humidity}')"

class Post_BME(db.Model):
    __tablename__ = 'post_BME'
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now())
    temperature = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False) 

    def __repr__(self):
        return f"Sensor('{self.date_posted}', '{self.temperature}', '{self.humidity}', '{self.pressure}', '{self.altitude}')"

class Post_TCS(db.Model):
    __tablename__ = 'post_TCS'
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now())
    red = db.Column(db.Float, nullable=False)
    green = db.Column(db.Float, nullable=False)
    blue = db.Column(db.Float, nullable=False)
    clr_temp = db.Column(db.Float, nullable=False)
    lux = db.Column(db.Float, nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False) 

    def __repr__(self):
        return f"Sensor('{self.date_posted}', '{self.red}', '{self.green}', '{self.blue}', '{self.clr_temp}', '{self.lux}')"

@app.route('/dht11', methods=['POST', 'GET'])
def dht11_page():
    if request.method == 'POST':
        a = request.get_data().decode('utf-8')
        data = json.loads(a)
        
        dic_circuits[data['cid']] = request.remote_addr
        
        iv = Sensor_Values_inClass(
            data['dht']['id'],
            data['dht']['name'],
            data['dht']['location'],
            data['dht']['temperature'],
            data['dht']['humidity'],
        )

        sensor_found = Sensor.query.filter_by(name=iv.name).first()
        post_author = Sensor.query.get(sensor_found.id)
        post_made_dht = Post_DHT(
            temperature=iv.temperature, 
            humidity=iv.humidity, 
            author=post_author, 
            date_posted=datetime.now()
        )

        db.session.add(post_made_dht)
        db.session.commit()
    return "Success"

@app.route('/inlab', methods=['POST', 'GET'])
def inlab_page():
    if request.method == 'POST':
        a = request.get_data().decode('utf-8')
        r2_data = json.loads(a)

        dic_circuits[r2_data['cid']] = request.remote_addr
        print(dic_circuits)

        sv = Sensor_Values_inLab(
            r2_data['tcs']['name'],
            r2_data['tcs']['id'],
            r2_data['tcs']['location'],
            round(r2_data['tcs']['red'],2),
            round(r2_data['tcs']['green'],2),
            round(r2_data['tcs']['blue'],2),
            round(r2_data['tcs']['clr_temp'],2),
            round(r2_data['tcs']['lux'],2),
            r2_data['bme']['name'],
            r2_data['bme']['id'],
            r2_data['bme']['location'],
            round(r2_data['bme']['temperature'],2),
            round(r2_data['bme']['pressure'],2),
            round(r2_data['bme']['altitude'],2),
            round(r2_data['bme']['humidity'],2),
        )

        sensor_found = Sensor.query.filter_by(name=sv.name_bme).first()
        post_author = Sensor.query.get(sensor_found.id)
        post_made_bme = Post_BME(
            temperature=sv.temperature,
            humidity=sv.humidity,
            pressure=sv.pressure,
            altitude=sv.altitude,
            author=post_author,
            date_posted=datetime.now()
        )

        sensor_found = Sensor.query.filter_by(name=sv.name_tcs).first()
        post_author = Sensor.query.get(sensor_found.id)
        post_made_tcs = Post_TCS(
            red=sv.red,
            green=sv.green,
            blue=sv.blue,
            clr_temp=sv.clr_temp,
            lux=sv.lux,
            author=post_author,
            date_posted=datetime.now()
        )

        db.session.add(post_made_bme)
        db.session.add(post_made_tcs)
        db.session.commit()
    # if method get, return html
    return "Success"



@app.route('/led', methods=["POST", "GET"])
def setLED():
    if request.method == "POST":
        circuit = None
        if (request.form.get("circuits") is None):
            return
        else:
            circuit = request.form.get("circuits")

        if (circuit[2] == "1"):
            if request.form.get("c1_redled"):
                c1_red_led_val = 1
            else:
                c1_red_led_val = 0

            if not (request.form["c1_blueled"]):
                c1_blue_led_val = 0
            else:
                c1_blue_led_val = int(request.form["c1_blueled"])

            data1 = json.dumps({
                    'redled': c1_red_led_val, 
                    'blueled': c1_blue_led_val
            })
            try:
                r1 = requests.post("http://" + dic_circuits[circuit] + '/led_set_post', data=data1)
            except KeyError:
                print("Key:",circuit,"does not exist.")
        elif (circuit[2] == "2"):
            if not (request.form["c2_redled"]):
                c2_red_led_val = 0
            else:
                c2_red_led_val = int(request.form["c2_redled"])

            if not (request.form["c2_greenled"]):
                c2_green_led_val = 0
            else:
                c2_green_led_val = int(request.form["c2_greenled"])

            if not (request.form["c2_blueled"]):
                c2_blue_led_val = 0
            else:
                c2_blue_led_val = int(request.form["c2_blueled"])

            data2 = json.dumps({
                    'redled': c2_red_led_val, 
                    'greenled': c2_green_led_val,
                    'blueled': c2_blue_led_val
                })
            
            try:
                r2 = requests.post("http://" + dic_circuits[circuit] + '/led_set_post', data=data2)
            except KeyError:
                print("Key:",circuit,"does not exist.")
        return render_template('LED_Commander.html')
    else:
        return render_template('LED_Commander.html')

@app.route('/system_info', methods=["POST", "GET"])
def show_latest_RGB():
    if request.method == "POST":
        if not (request.form["X_ID"] and request.form["Y_DATA"]):
            return
        else:
            X = int(request.form["X_ID"])
            Y = int(request.form["Y_DATA"])
            sensor_type = X % 3 # 0 -> BME, 1 -> DHT, 2 -> TCS

            if (sensor_type == 0): # BME
                circuit_2_data = db.session.query(Post_BME).filter(Post_BME.sensor_id == X).order_by(db.desc('date_posted')).all()
            elif(sensor_type == 1): #DHT
                circuit_2_data = db.session.query(Post_DHT).filter_by(sensor_id=int(X)).order_by(db.desc('date_posted')).all() 
            else: #TCS 
                circuit_2_data = db.session.query(Post_TCS).filter_by(sensor_id=X).order_by(db.desc('date_posted')).all()

            rows=[]
            indices=[]

            for i in range(Y):
                row = circuit_2_data[i]
                if (sensor_type == 0): # BME
                    rows.append([row.temperature, row.pressure, row.altitude, row.humidity, row.sensor_id]) # Change the elements
                    indices.append(row.date_posted)
                elif(sensor_type == 1): #DHT
                    rows.append([row.temperature, row.humidity, row.sensor_id]) # Change the elements
                    indices.append(row.date_posted)
                else: #TCS 
                    rows.append([row.red, row.green, row.blue, row.clr_temp, row.lux, row.sensor_id]) # Change the elements
                    indices.append(row.date_posted)

            if (sensor_type == 0): # BME
                df = pd.DataFrame(data=rows, columns=["Temperature", "Pressure", "Altitude", "Humidity","Sensor ID"], index=indices) # Fix
            elif (sensor_type == 1): #DHT
                df = pd.DataFrame(data=rows, columns=["Temperature", "Humidity", "Sensor ID"], index=indices) # Fix
            else: #TCS 
                df = pd.DataFrame(data=rows, columns=["R", "G", "B", "Color Temperature (K)", "Intensity (Lux)", "Sensor ID"], index=indices) # Fix

            df_html = df.to_html(col_space='65px').replace('<td>', '<td align="center">')

            return render_template('system_info.html', table_html=df_html) # Change name
    else:
        return render_template('system_info.html')

if __name__ == '__main__':
    app.run(debug=False, host='192.168.137.1')