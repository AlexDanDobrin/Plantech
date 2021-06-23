from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initializare aplicatie
app = Flask(__name__)
app.config['SECRET_KEY'] = 'HopeForTheBestPrepareForTheWorst'

basedir = os.path.abspath(os.path.dirname(__file__))

# DEMO are doar rol de prezentare nu face parte din modul de lucru al lucrarii de licenta
DEMO = False

# Creare baza de date
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initializare baza de date
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(30), unique = True)
    password = db.Column(db.String(128))
    sensors = db.relationship('Sensor', backref = 'user', lazy = 'dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    mode = db.Column(db.String(10))
    limit = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    measurements = db.relationship('Measurement', backref = 'sensor', lazy = 'dynamic')

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'))
    value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)

    def __init__(self, sensor_id, value):
        self.sensor_id = sensor_id
        self.value = value
        self.timestamp = datetime.now()

@app.route('/', methods=['GET'])
def index():
    return jsonify({'msg': 'Hello'})

# Endpoint-urile aplicatiei iOS

@app.route('/startDEMO', methods=['GET'])
def set_demo():
    global DEMO 
    DEMO = True
    return jsonify({'message': 'DEMO to be started!'}), 200

@app.route('/register', methods=['POST'])
def create_user():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if user is None:
        new_user = User(username, generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'New user sucessfully created!'}), 201
    
    return jsonify({'message': 'User already exists!'}), 400
    

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({'message': 'Invalid username or password!'}), 404

    return jsonify({'message': 'Successfully logged in!'}), 200


@app.route('/lastMeasurement/<target_sensor_id>', methods=['GET'])
def get_last_measurement(target_sensor_id):
    measurement = Measurement.query.filter_by(sensor_id=target_sensor_id).order_by(Measurement.timestamp.desc()).first()
    print(measurement.timestamp)

    if not measurement:
        return jsonify({'message': 'Invalid sensor id or no measurements for given sensor!'}), 404
        
    measurement_data = {}
    measurement_data['sensorID'] = measurement.sensor_id
    measurement_data['measurementID'] = measurement.id
    measurement_data['value'] = measurement.value
    measurement_data['timestamp'] = measurement.timestamp

    return jsonify(measurement_data)

@app.route('/getMeasurements/<target_sensor_id>', methods=['GET'])
def get_measurements(target_sensor_id):
    measurements = Measurement.query.filter_by(sensor_id=target_sensor_id)

    if not measurements:
        return jsonify({'message': 'Invalid sensor id or no measurements for given sensor!'}), 404
    
    output = []

    for measurement in measurements:
        measurement_data = {}
        measurement_data['sensorID'] = measurement.sensor_id
        measurement_data['measurementID'] = measurement.id
        measurement_data['value'] = measurement.value
        measurement_data['timestamp'] = measurement.timestamp
        output.append(measurement_data)

    return jsonify(output)

# Endpoint-urile Raspberry-ului

# DEMO pentru a actiona pompa de apa la comanda
# Doar pentru prezentarea licentei
@app.route('/startDEMO', methods=['GET'])
def start_demo():
    global DEMO
    if DEMO == True:
        DEMO = False
        return jsonify({'message': 'START DEMO!'}), 200
    
    return jsonify({'message': 'DEMO not requested.'}), 400

@app.route('/getWorkMode/<target_sensor_id>', methods=['GET'])
def get_work_mode(target_sensor_id):
    sensor = Sensor.query.filter_by(id=target_sensor_id).first()
    
    if sensor is None:
        return jsonify({'message': 'Invalid sensor id!'}), 404

    output = {}
    output['auto'] = sensor.mode
    return jsonify(output)

@app.route('/getTreshold/<target_sensor_id>', methods=['GET'])
def get_treshold(target_sensor_id):
    sensor = Sensor.queyr.filter_by(id=target_sensor_id).first()

    if sensor is None:
        return jsonify({'message': 'Invalid sensor id!'}), 404


@app.route('/newMeasurement/<target_sensor_id>', methods=['POST'])
def add_measurement(target_sensor_id):
    # Requestul trimis de la Raspberry este de tip application/x-www-form-urlencoded
    # Acelasi tip de request este folosit si de la aplicatia iOS catre API

    value_from_sensor = request.form.get('value')
    
    sensor = Sensor.query.filter_by(id=target_sensor_id).first()
    if sensor is None:
        return jsonify({'message': 'Sensor does not exist in records'}), 404

    new_measurement = Measurement(target_sensor_id, value_from_sensor)
    db.session.add(new_measurement)
    db.session.commit()

    return jsonify({'message': 'New measurement succesfully added!'}), 201

# Porneste serverul
if __name__ == '__main__':
    app.run()