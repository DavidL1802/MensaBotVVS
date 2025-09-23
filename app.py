#!/usr/bin/env python3
"""
Flask web application for displaying VVS departures.

Shows real-time departure information for the "Universität" stop.
"""

from flask import Flask, render_template, jsonify
from datetime import datetime
import logging

from tools import listDepartures

app = Flask(__name__, template_folder='web_templates')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Universität stop ID
UNIVERSITAET_STOP_ID = "de:08111:6008"
STOP_NAME = "Universität"


def get_departures_data():
    """
    Fetch current departures for Universität stop.
    
    Returns:
        List of departure dictionaries for template rendering
    """
    try:
        departures = listDepartures(
            stopId=UNIVERSITAET_STOP_ID,
            numberOfResults=20
        )
        
        # Convert departures to dictionaries for template rendering
        departures_data = []
        for dep in departures:
            departure_dict = {
                'line': dep.line,
                'destination': dep.destination,
                'scheduled_time': dep.scheduledTime.strftime("%H:%M"),
                'display_time': dep.displayTime,
                'delay_text': dep.delayText,
                'delay_minutes': dep.delayMinutes or 0,
                'platform': dep.platform or '-',
                'transport_mode': dep.transportMode.value,
                'realtime': dep.realtime
            }
            departures_data.append(departure_dict)
        
        return departures_data
        
    except Exception as e:
        logger.error(f"Error fetching departures: {e}")
        return []


@app.route('/')
def index():
    """Homepage showing departure table."""
    departures = get_departures_data()
    last_updated = datetime.now().strftime("%H:%M:%S")
    
    return render_template(
        'index.html',
        departures=departures,
        stop_name=STOP_NAME,
        last_updated=last_updated
    )


@app.route('/api/departures')
def api_departures():
    """API endpoint to get fresh departure data (for AJAX refresh)."""
    departures = get_departures_data()
    last_updated = datetime.now().strftime("%H:%M:%S")
    
    return jsonify({
        'departures': departures,
        'last_updated': last_updated,
        'stop_name': STOP_NAME
    })


if __name__ == '__main__':
    # Create web_templates and static directories if they don't exist
    import os
    os.makedirs('web_templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5001)