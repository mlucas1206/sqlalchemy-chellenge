# Import the dependencies.
from flask import Flask, jsonify, make_response

#sqlalchemy
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

#other dependencies
import datetime as dt

# create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite?check_same_thread=False")
#https://stackoverflow.com/questions/34009296/using-sqlalchemy-session-from-flask-raises-sqlite-objects-created-in-a-thread-c

#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session =Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
#homepage
@app.route("/")
#List all available routes
def home():
    html = '''<h1>Welcome to the Hawaii Weather Station</h1>
    <h2>Please see available links for our jsonified data between</br>
    2010-01-01 and 2017-08-23</h2>
    </br>
    <a href = "/api/v1.0/precipitation">Precipitation for the past year</a>
        <ul>
            <li>This will show the latest 12 months of precipitation.</li>
            <li>You can also input this manually:  /api/v1.0/precipitation</li>
        </ul> 
   
    <a href = "/api/v1.0/stations">List of stations</a>
        <ul>
            <li>This is our database for our existing stations.</li>
            <li>You can also input this manually:  /api/v1.0/stations</li>
        </ul> 

    <a href = "/api/v1.0/tobs">List of tobs</a>
        <ul>
            <li>This will show tobs in the recent 12 months by the most active station.</li>
            <li>You can also input this manually:  /api/v1.0/tobs</li>
        </ul> 

    <p>Start Date:<p>
        <form action="/api/v1.0/<start>" method="GET">
        <input type="text" name="start">
        <input type="submit" value="Submit">


    '''
    return(html)

#precipitation
@app.route("/api/v1.0/precipitation")
#dictionary date and prcp and jsonify
def precipitation():    
    # Find most recent data
    date_sorted = session.query(measurement.date).order_by(measurement.date.desc())
    # Starting from the most recent data point in the database. 
    first_date = dt.datetime.strptime(date_sorted.first()[0],'%Y-%m-%d').date()
    print(first_date)
    # Calculate the date one year from the last date in data set.
    t12 = first_date - dt.timedelta(days = 365)
    print(t12)
    # Perform a query to retrieve the data and precipitation scores
    prec_sel = [measurement.date, measurement.prcp]
    prec_data_order = session.query(*prec_sel).\
        filter(measurement.date >= str(t12), measurement.prcp != None).\
            order_by(measurement.date).all()
    prcp_dict = [dict(x) for x in prec_data_order]

    return jsonify(prcp_dict)

#stations list
@app.route("/api/v1.0/stations")
#list of stations jsonified
def stations():
    stations = session.query(station.station, station.name)
    station_dict = [dict(x) for x in stations]
    return jsonify(station_dict)

#tobs list
@app.route("/api/v1.0/tobs")
def tobs():
    # Find most recent data
    date_sorted = session.query(measurement.date).order_by(measurement.date.desc())
    # Starting from the most recent data point in the database. 
    first_date = dt.datetime.strptime(date_sorted.first()[0],'%Y-%m-%d').date()
    print(first_date)
    # Calculate the date one year from the last date in data set.
    t12 = first_date - dt.timedelta(days = 365)
    #Get the count per station
    station_count = session.query(measurement.station, func.count(measurement.station)).group_by(measurement.station).\
    order_by(func.count(measurement.station).desc()).all()
    #Get the top station data
    tobs_top = session.query(measurement.station, measurement.tobs).\
    filter(measurement.station == station_count[0][0],measurement.date >= str(t12), measurement.prcp != None).all()
    #Return the instances for the top station
    tobs_dict = [dict(x) for x in tobs_top]
    return jsonify(tobs_dict)


#specying date onwards
@app.route("/api/v1.0/<start>")
#JSON list of min max and avg temp from <start> to the most recent
def start(start):
    #Catch wrong formats
    dates = [x[0] for x in session.query(measurement.date)]
    if start in dates:
        print(dt.datetime.strptime(start,'%Y-%m-%d').date())
        # date inputted in <start> becomes current date 
        #make a selector for min, max, and avg
        active_sel = [
            func.min(measurement.tobs), 
            func.max(measurement.tobs), 
            func.avg(measurement.tobs)
            ]

        #query for data from start date till most recent
        active_query = session.query(*active_sel).filter(measurement.date >= start)
        #return dictionary of query
        start_dict = [
            {   
                'from_date': start,
                "min_temp": row[0],
                "max_temp": row[1],
                "avg_temp": row[2]
            }
            for row in active_query
            ]
        
        return jsonify(start_dict)
    
    # Say to put proper format
    else:
        return(f'Invalid date.</br>' 
               f'Please make sure that the dates are in </br>'
               f'YYYY-MM-DD format and are between 2010-01-01 to 2017-08-23.')


#specifying date to date
@app.route("/api/v1.0/<start>/<end>")
    #JSON list of min max and avg temp from <start> to the <end> inclusive
def start_end(start, end):
    # range is <start> to <end>
     #Catch wrong formats
    dates = [x[0] for x in session.query(measurement.date)]
    if start in dates and end in dates:     
        #make a selector for min, max, and avg
        active_sel = [
            measurement.date,
            func.min(measurement.tobs), 
            func.max(measurement.tobs), 
            func.avg(measurement.tobs)
            ]

        #query for data from start date till most recent
        active_query = session.query(*active_sel).filter(measurement.date >= start, measurement.date <= end)
        #return dictionary of query
        start_end_dict = [
            {   
                'from_date': start,
                'to-date': end,
                "min_temp": row[0],
                "max_temp": row[1],
                "avg_temp": row[2]
            }
            for row in active_query
            ]
        
        return jsonify(start_end_dict)
    else:
        return(f'Invalid date.</br>' 
               f'Please make sure that the dates are in </br>'
               f'YYYY-MM-DD format and are between 2010-01-01 to 2017-08-23.')


if __name__ == '__main__':
    app.run(debug=True)



# TODOS
# Finish Homepage
# Try and put links and inputs in the homepage