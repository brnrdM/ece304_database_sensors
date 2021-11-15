from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from dataclasses import dataclass

@dataclass
class Sensor_Values_inClass:
    id: str
    location_dht: str
    temperature: float
    humidity: float

@dataclass
class Sensor_Values_inLab:
    id_tcs: str
    location_tcs: str
    red: float
    green: float
    blue: float
    clr_temp: float
    lux: float
    id_bme: str
    location_bme: str
    temperature: float
    pressure: float
    altitude: float 
    humidity: float

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
        iv = Sensor_Values_inClass(
            data['id'],
            data['Location'],
            data['Temperature'],
            data['Humidity'],
        )

        sensor_found = Sensor.query.filter_by(name=iv.id).first()
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
        
        sv = Sensor_Values_inLab(
            r2_data['tcs']['id'],
            r2_data['tcs']['location'],
            round(r2_data['tcs']['red'],2),
            round(r2_data['tcs']['green'],2),
            round(r2_data['tcs']['blue'],2),
            round(r2_data['tcs']['clr_temp'],2),
            round(r2_data['tcs']['lux'],2),
            r2_data['bme']['id'],
            r2_data['bme']['location'],
            round(r2_data['bme']['temperature'],2),
            round(r2_data['bme']['pressure'],2),
            round(r2_data['bme']['altitude'],2),
            round(r2_data['bme']['humidity'],2),
        )

        sensor_found = Sensor.query.filter_by(name=sv.id_tcs).first()
        post_author = Sensor.query.get(sensor_found.id)
        post_made_bme = Post_BME(
            temperature=sv.temperature,
            humidity=sv.humidity,
            pressure=sv.pressure,
            altitude=sv.altitude,
            author=post_author,
            date_posted=datetime.now()
        )

        sensor_found = Sensor.query.filter_by(name=sv.id_bme).first()
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

@app.route('/')
def main_page():
    latest_dht_records = \
        db.session.\
        query(Post_DHT).\
        order_by(db.desc('date_posted')).\
        limit(1).\
        all()

    latest_bme_records = \
        db.session.\
        query(Post_BME).\
        order_by(db.desc('date_posted')).\
        limit(1).\
        all()

    latest_tcs_records = \
        db.session.\
        query(Post_TCS).\
        order_by(db.desc('date_posted')).\
        limit(1).\
        all()

    sensor_entries = \
        db.session.\
        query(Sensor).\
        order_by(db.asc('id')).\
        all()
    
    dht_sensor = latest_dht_records[0]
    bme_sensor = latest_bme_records[0]
    tcs_sensor = latest_tcs_records[0]

    iv = Sensor_Values_inClass(
        dht_sensor.id,
        sensor_entries[0].location,
        dht_sensor.temperature,
        dht_sensor.humidity
    )

    sv = Sensor_Values_inLab(
        tcs_sensor.id,
        sensor_entries[1].location,
        tcs_sensor.red,
        tcs_sensor.green,
        tcs_sensor.blue,
        tcs_sensor.clr_temp,
        tcs_sensor.lux,
        bme_sensor.id,
        sensor_entries[2].location,
        bme_sensor.temperature,
        bme_sensor.pressure,
        bme_sensor.altitude,
        bme_sensor.humidity
    )


    return render_template('Climate_Information.html', iv=iv, sv=sv)

@app.route('/bme')
def get_information_bme():
    latest_bme_records = \
        db.session.\
        query(Post_BME).\
        order_by(db.desc('date_posted')).\
        limit(1).\
        all()

    sensor_entries = \
        db.session.\
        query(Sensor).\
        order_by(db.asc('id')).\
        all()

    bme_sensor = latest_bme_records[0]

    sv = Sensor_Values_inLab(
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        bme_sensor.id,
        sensor_entries[2].location,
        bme_sensor.temperature,
        bme_sensor.pressure,
        bme_sensor.altitude,
        bme_sensor.humidity
    )

    return render_template('bme.html', sv=sv)


@app.route('/tcs')
def get_information_tcs():
    latest_tcs_records = \
        db.session.\
        query(Post_TCS).\
        order_by(db.desc('date_posted')).\
        limit(1).\
        all()

    sensor_entries = \
        db.session.\
        query(Sensor).\
        order_by(db.asc('id')).\
        all()

    tcs_sensor = latest_tcs_records[0]

    sv = Sensor_Values_inLab(
        tcs_sensor.id,
        sensor_entries[1].location,
        tcs_sensor.red,
        tcs_sensor.green,
        tcs_sensor.blue,
        tcs_sensor.clr_temp,
        tcs_sensor.lux,
        None,
        None,
        None,
        None,
        None,
        None
    )

    return render_template('tcs.html', sv=sv)

# 192.168.0.4:5000/bme_x?rows=10
@app.route('/bme_x', methods=['GET'])
def get_information_bme_last_x():
    rows = 0
    if request.method == 'GET':
        rows = request.args.get('rows')

        if (not rows):
            rows = 10

        latest_bme_records = \
            db.session.\
            query(Post_BME).\
            order_by(db.desc('date_posted')).\
            limit(rows).\
            all()

        sensor_entries = \
            db.session.\
            query(Sensor).\
            order_by(db.asc('id')).\
            all()
        
        table_string = \
        "<tr>"\
        "<th>Date Time </th>"\
        "<th>Temperature (C) </th>"\
        "<th>Pressure (hPa) </th>"\
        "<th>Altitude (m) </th>"\
        "<th>Humidity (%) </th>"\
        "</tr>"

        for bme_sensor in latest_bme_records:
            sv = Sensor_Values_inLab(
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                bme_sensor.id,
                sensor_entries[2].location,
                bme_sensor.temperature,
                bme_sensor.pressure,
                bme_sensor.altitude,
                bme_sensor.humidity
            )
            table_string += "<tr>"
            table_string += f"<th>{bme_sensor.date_posted}</th>"
            table_string += f"<th>{sv.temperature}</th>"
            table_string += f"<th>{sv.pressure}</th>"
            table_string += f"<th>{sv.altitude}</th>"
            table_string += f"<th>{sv.humidity}</th>"
            table_string += "</tr>"

        return render_template('bme_x.html', sv=sv, table_string=table_string)
    else:
        return "Fail"

# http://192.168.0.4:5000/tcs_x?rows=10
@app.route('/tcs_x', methods=['GET'])
def get_information_tcs_last_x():
    rows = 0
    if request.method == 'GET':
        rows = request.args.get('rows')

        if (not rows):
            rows = 10

        latest_tcs_records = \
            db.session.\
            query(Post_TCS).\
            order_by(db.desc('date_posted')).\
            limit(rows).\
            all()

        sensor_entries = \
            db.session.\
            query(Sensor).\
            order_by(db.asc('id')).\
            all()
        
        table_string = \
        "<tr>"\
        "<th>Date Time </th>"\
        "<th>Red (0-255) </th>"\
        "<th>Green (0-255) </th>"\
        "<th>Blue (0-255) </th>"\
        "<th>Color Temp </th>"\
        "<th>Lux </th>"\
        "</tr>"

        for tcs_sensor in latest_tcs_records:
            sv = Sensor_Values_inLab(
                tcs_sensor.id,
                sensor_entries[1].location,
                tcs_sensor.red,
                tcs_sensor.green,
                tcs_sensor.blue,
                tcs_sensor.clr_temp,
                tcs_sensor.lux,
                None,
                None,
                None,
                None,
                None,
                None
            )
            table_string += "<tr>"
            table_string += f"<th>{tcs_sensor.date_posted}</th>"
            table_string += f"<th>{sv.red}</th>"
            table_string += f"<th>{sv.green}</th>"
            table_string += f"<th>{sv.blue}</th>"
            table_string += f"<th>{sv.clr_temp}</th>"
            table_string += f"<th>{sv.lux}</th>"
            table_string += "</tr>"

        return render_template('tcs_x.html', sv=sv, table_string=table_string)
    else:
        return "Fail"


if __name__ == '__main__':
    app.run(debug=False, host='10.250.95.189')