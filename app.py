# Import the dependencies.
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, text
import datetime as dt
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with = engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    return(
    f"Available Routes:<br/>"
    f"/api/v1.0/precipitation<br/>"
    f"/api/v1.0/stations<br/>"
    f"/api/v1.0/tobs<br/>"
    f"/api/v1.0/<start><br/>"
    f"/api/v1.0/<start>/<end>"
)

@app.route('/api/v1.0/precipitation')
def precipitation():
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_12_months = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d') - dt.timedelta(days = 365)
    last_12_months_data = session.query(Measurement.date,Measurement.prcp).\
        filter(Measurement.date > last_12_months).\
        filter(Measurement.date <= most_recent_date[0]).\
        all()
    prcp_list = []
    for date, prcp in last_12_months_data:
        data_dict = {}
        data_dict["date"] = date
        data_dict["precipitation"] = prcp
        prcp_list.append(data_dict)
    return jsonify(prcp_list)

@app.route("/api/v1.0/stations")
def station():
    station_list = []
    station_data = session.query(Station.station, Station.name, Station.latitude,\
                                Station.longitude, Station.elevation).all()
    for station_id, name, latitude, longitude, elevation in station_data:
        station_dict = {}
        station_dict["station_id"] = station_id
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        station_list.append(station_dict)
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
    tobs_data_list = []
    station_act_count = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).\
        all()
    latest_date = session.query(Measurement.date).\
        order_by(Measurement.date.desc()).\
        filter(Measurement.station == station_act_count[0][0]).\
        first()
    station_last_12_months = dt.datetime.strptime(latest_date[0], '%Y-%m-%d') - dt.timedelta(days = 365)
    station_last_12_months_data = session.query(Measurement.date,Measurement.tobs).\
        filter(Measurement.date > station_last_12_months).\
        filter(Measurement.date <= latest_date[0]).\
        filter(Measurement.station == station_act_count[0][0]).\
        all()
    for date, temp in station_last_12_months_data:
        active_station_data = {}
        active_station_data["date"] = date
        active_station_data["temp"] = temp
        tobs_data_list.append(active_station_data)
    return jsonify(tobs_data_list)

@app.route("/api/v1.0/<start>")
def start_date_data(start):
    try:
        dt.datetime.fromisoformat(start)
        most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
        earliest_date = session.query(Measurement.date).order_by(Measurement.date).first()
        if start > most_recent_date[0]:
            return(f"Invalid Starting Date: Larger than most recent date ({most_recent_date[0]})")
        if start < earliest_date[0]:
            return(f"Invalid Starting Date: Smaller than earliest date ({earliest_date[0]})")
        date_data = session.query(Measurement.tobs).\
            filter(Measurement.date >= start).all()
        date_data_list = [x[0] for x in date_data]
        date_data_dict = {}
        date_data_dict["TMIN"] = min(date_data_list)
        date_data_dict["TAVG"] = sum(date_data_list)/\
            len(date_data_list)
        date_data_dict["TMAX"] = max(date_data_list)
        return jsonify(date_data_dict)
    except ValueError:
        return ("Invalid Date Format<br/>(must be in YYYY-MM-DD)")

@app.route("/api/v1.0/<start>/<end>")
def start_end_date_data(start,end):
    try:
        dt.date.fromisoformat(start)
        dt.date.fromisoformat(end)
        most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
        earliest_date = session.query(Measurement.date).order_by(Measurement.date).first()
        if start > most_recent_date[0]:
            return(f"Invalid Starting Date: Larger than most recent date ({most_recent_date[0]})")
        if start < earliest_date[0]:
            return(f"Invalid Starting Date: Smaller than earliest date ({earliest_date[0]}")
        if end > most_recent_date[0]:
            return(f"Invalid Ending Date: Larger than most recent date ({most_recent_date[0]})")
        if end < earliest_date[0]:
            return(f"Invalid Ending Date: Smaller than earliest date ({earliest_date[0]})")
        if end < start:
            return('Invalid Dates: ending date smaller than starting date')
        date_data = session.query(Measurement.tobs).\
            filter(Measurement.date >= start).\
            filter(Measurement.date <= end).\
            all()
        date_data_list = [x[0] for x in date_data]
        date_data_dict = {}
        date_data_dict["TMIN"] = min(date_data_list)
        date_data_dict["TAVG"] = sum(date_data_list)/\
            len(date_data_list)
        date_data_dict["TMAX"] = max(date_data_list)
        return jsonify(date_data_dict)
    except ValueError:
        return ("Invalid Date Format<br/>(must be in YYYY-MM-DD)")

if __name__ == "__main__":
    app.run(debug=True)