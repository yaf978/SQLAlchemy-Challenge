from scipy import stats
from datetime import datetime
import datetime as dt
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import sqlalchemy
import numpy as np


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurements = Base.classes.measurement
Stations = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Surf's Up Climate API!<br/>"
        f"Routes:<br/>"
        f"<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"<br/>"
        f"Most recent 365-day tobs for dataset's most active station:<br/>"
        f"/api/v1.0/tobs<br/>"
        f"<br/>"
        f"For min/avg/max tobs following specific date (specify year-month-day in format shown, inclusive):<br/>"
        f"/api/v1.0/yyyy-mm-dd<br/>"
        f"<br/>"
        f"For min/avg/max tobs between specific dates (specify year-month-day in format shown, begin date/end date, inclusive):<br/>"
        f"/api/v1.0/yyyy-mm-dd/yyyy-mm-dd"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a dictionary of all precipitation for the past year"""
    # Query all precipitation records for the past year
    last_date = session.query(Measurements.date).order_by(
        Measurements.date.desc()).first()
    last_date = dt.datetime.strptime(last_date[0], '%Y-%m-%d')
    year_ago = last_date - dt.timedelta(days=366)
    last_year = session.query(Measurements.date, Measurements.prcp).\
        filter(Measurements.date > year_ago).all()
    session.close()

    # Convert list to dictionary
    all_precipitation = []
    for date, prcp in last_year:
        precip_dict = {}
        precip_dict[date] = prcp
        all_precipitation.append(precip_dict)

    # Return JSON representation of dictionary
    return jsonify(all_precipitation)


@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all stations"""
    # Query all station records
    station_list = session.query(Stations.station,
                                 Stations.name,
                                 Stations.latitude,
                                 Stations.longitude,
                                 Stations.elevation).all()
    session.close()

    # Create a dictionary from the station row data and append to a list of all_stations
    all_stations = []
    for station, name, latitude, longitude, elevation in station_list:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    # Return JSON representation of list
    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all temperature observations for the most active station (USC00519281) for the past year"""
    # Query the last 12 months of temperature observation data for this station
    last_date = session.query(Measurements.date).order_by(
        Measurements.date.desc()).first()
    last_date = dt.datetime.strptime(last_date[0], '%Y-%m-%d')
    year_ago = last_date - dt.timedelta(days=366)
    last_year_active = session.query(Measurements.date, Measurements.tobs).\
        filter(Measurements.date > year_ago).\
        filter(Measurements.station == 'USC00519281').all()
    session.close()

    # Create a dictionary from the station's tobs data and append to a list of all_tobs
    all_tobs = []
    for date, tobs in last_year_active:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        all_tobs.append(tobs_dict)

    # Return JSON representation of list
    return jsonify(all_tobs)


@app.route("/api/v1.0/<start>")
def start(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of min, avg, and max temp records post-user start date"""
    # Query temperature observation data post-start date
    start_date = dt.datetime.strptime(start, '%Y-%m-%d')

    tobs_min = session.query(Measurements.station,
                             Stations.name,
                             Measurements.date,
                             func.min(Measurements.tobs)).\
        filter(Measurements.station == Stations.station).\
        filter(Measurements.date >= start_date).all()

    tobs_avg = session.query(Measurements.station,
                             Stations.name,
                             Measurements.date,
                             func.avg(Measurements.tobs)).\
        filter(Measurements.station == Stations.station).\
        filter(Measurements.date >= start_date).all()

    tobs_max = session.query(Measurements.station,
                             Stations.name,
                             Measurements.date,
                             func.max(Measurements.tobs)).\
        filter(Measurements.station == Stations.station).\
        filter(Measurements.date >= start_date).all()

    session.close()

    # Create a dictionary from the min-avg-max tobs data and append to a list
    min_avg_max = []

    for station, name, date, tobs in tobs_min:
        min_dict = {}
        min_dict["station"] = station
        min_dict["name"] = name
        min_dict["date"] = date
        min_dict["minimum tobs"] = tobs
        min_avg_max.append(min_dict)

    for station, name, date, tobs in tobs_avg:
        avg_dict = {}
        avg_dict["station"] = station
        avg_dict["name"] = name
        avg_dict["date"] = date
        avg_dict["average tobs"] = round(tobs, 1)
        min_avg_max.append(avg_dict)

    for station, name, date, tobs in tobs_max:
        max_dict = {}
        max_dict["station"] = station
        max_dict["name"] = name
        max_dict["date"] = date
        max_dict["maximum tobs"] = tobs
        min_avg_max.append(max_dict)

    # Return JSON representation of list
    return jsonify(min_avg_max)


@app.route("/api/v1.0/<start>/<end>")
def tween(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of min, avg, and max temp records between user start/end dates"""
    # Query temperature observation data between user dates
    start_date = dt.datetime.strptime(start, '%Y-%m-%d')
    end_date = dt.datetime.strptime(end, '%Y-%m-%d')

    tobs_min = session.query(Measurements.station,
                             Stations.name,
                             Measurements.date,
                             func.min(Measurements.tobs)).\
        filter(Measurements.station == Stations.station).\
        filter(Measurements.date.between(start_date, end_date)).all()

    tobs_avg = session.query(Measurements.station,
                             Stations.name,
                             Measurements.date,
                             func.avg(Measurements.tobs)).\
        filter(Measurements.station == Stations.station).\
        filter(Measurements.date.between(start_date, end_date)).all()

    tobs_max = session.query(Measurements.station,
                             Stations.name,
                             Measurements.date,
                             func.max(Measurements.tobs)).\
        filter(Measurements.station == Stations.station).\
        filter(Measurements.date.between(start_date, end_date)).all()

    session.close()

    # Create a dictionary from the min-avg-max tobs data and append to a list
    min_avg_max = []

    for station, name, date, tobs in tobs_min:
        min_dict = {}
        min_dict["station"] = station
        min_dict["name"] = name
        min_dict["date"] = date
        min_dict["minimum tobs"] = tobs
        min_avg_max.append(min_dict)

    for station, name, date, tobs in tobs_avg:
        avg_dict = {}
        avg_dict["station"] = station
        avg_dict["name"] = name
        avg_dict["date"] = date
        avg_dict["average tobs"] = round(tobs, 1)
        min_avg_max.append(avg_dict)

    for station, name, date, tobs in tobs_max:
        max_dict = {}
        max_dict["station"] = station
        max_dict["name"] = name
        max_dict["date"] = date
        max_dict["maximum tobs"] = tobs
        min_avg_max.append(max_dict)

    # Return JSON representation of list
    return jsonify(min_avg_max)


if __name__ == "__main__":
    app.run(debug=True)
