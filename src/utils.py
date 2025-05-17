import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom
from datetime import datetime
from typing import List, Tuple, Optional
import pytz
import re

TRIAS_URL = "https://efastatic.vvs.de/unistuttgart/trias"
REQUESTOR_REF = "uni0719"

namespaces = {
    'trias': 'http://www.vdv.de/trias',
    'siri': 'http://www.siri.org.uk/siri',
    'acsb': 'http://www.ifopt.org.uk/acsb',
    'ifopt': 'http://www.ifopt.org.uk/ifopt',
    'datex2': 'http://datex2.eu/schema/1_0/1_0'
}


def loadTemplate(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def fillTemplate(template: str, values: dict) -> str:
    for key, val in values.items():
        template = template.replace(f"{{{{{key}}}}}", val)
    return template

def convertISODuration(duration: str) -> str:
    """
    Convert ISO time to a specific format.

    Args:
        time (str): The ISO time string to convert.

    Returns:
        str: The converted time string.
    """
    # Extract minutes using regex
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)

    if match:
        hours = match.group(1)
        minutes = match.group(2)
        seconds = match.group(3)

        parts = []
        if hours:
            parts.append(f"{int(hours)} hr")
        if minutes:
            parts.append(f"{int(minutes)} min")
        if seconds:
            parts.append(f"{int(seconds)} sec")

        formatted_duration = " ".join(parts)
        return formatted_duration

def findStops(name: str) -> Optional[List[Tuple[str, str, str]]]:
    """
    Find the stop name in the given string.

    Args:
        name (str): The string to search for the stop name.

    Returns:
        Optional[List[Tuple[str, str, str]]]: A list of triples (stop name, location name, stop point reference) if found, otherwise None.
    """
    template = loadTemplate("xml_templates/locationInformation_request.xml")
    xml_request = fillTemplate(template, {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "requestor_ref": REQUESTOR_REF,
        "location": name,
    })

    headers = {
        "Content-Type": "text/xml"
    }

    # Send request
    response = requests.post(TRIAS_URL, data=xml_request.encode("utf-8"), headers=headers)
    response.encoding = 'utf-8'

    # Process response
    if response.status_code == 200:
        # Parse the XML
        root = ET.fromstring(response.text)

        # Find all Location elements
        elements = root.findall('.//trias:Location', namespaces)

        stopNamesAndIDs = []

        for element in elements:
            # Get all stop point names
            stopPointNames = element.findall('.//trias:StopPointName/trias:Text', namespaces)

            if stopPointNames is not None:
                locations = element.findall('.//trias:LocationName/trias:Text', namespaces)
                stopPointRefs = element.findall('.//trias:StopPointRef', namespaces)
                for index, stop in enumerate(stopPointNames):
                    stopNamesAndIDs.append((stop.text, locations[index].text, stopPointRefs[index].text))
        
        return stopNamesAndIDs
    else:
        print("❌ Error fetching data")
        print("Status Code:", response.status_code)
        return None
    
def requestTrip(startRef: str, stopRef: str, time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")) -> Optional[List[Tuple[str, str, str]]]:
    """
    Request a trip from the start reference to the stop reference.

    Args:
        startRef (str): The start reference.
        stopRef (str): The stop reference.

    Returns:
        Optional[List[Tuple[str, str, str]]]: A list of tuples containing the trip information if successful, otherwise None.
    """
    template = loadTemplate("xml_templates/trip_request.xml")
    xml_request = fillTemplate(template, {
        "timestamp": time,
        "requestor_ref": REQUESTOR_REF,
        "start_ref": startRef,
        "stop_ref": stopRef,
    })

    headers = {
        "Content-Type": "text/xml"
    }

    # Send request
    response = requests.post(TRIAS_URL, data=xml_request.encode("utf-8"), headers=headers)
    response.encoding = 'utf-8'

    try:
        dom = xml.dom.minidom.parseString(response.text)
        pretty_response = dom.toprettyxml(indent="  ")
    except Exception as e:
        print("Error parsing XML response:", e)
        pretty_response = response.text  # fallback to raw

    with open("formatted_response.xml", "w", encoding="utf-8") as f:
        f.write(pretty_response)

    # Process response
    if response.status_code == 200:
        # Parse the XML
        root = ET.fromstring(response.text)
        # Find all Trip elements
        tripResults = root.findall('.//trias:TripResult', namespaces)
        trips = []

        if tripResults is None:
            print("❌ No trip results found")
            return None
        else:
            for index, result in enumerate(tripResults):
                trip = {}
                trip["duration"] = convertISODuration(result.find('.//trias:Trip/trias:Duration', namespaces).text)
                trip["interchanges"] = int(result.find('.//trias:Trip/trias:Interchanges', namespaces).text if result.find('.//trias:Trip/trias:Interchanges', namespaces) is not None else 0)

                for leg in result.findall('.//trias:Trip/trias:TripLeg', namespaces):
                    if leg.find('.//trias:LegId', namespaces).text == "1":
                        trip["startLocation"] = leg.find('.//trias:TimedLeg/trias:LegBoard/trias:StopPointName/trias:Text', namespaces).text
                        trip["departureTimeTable"] = pytz.utc.localize(datetime.strptime(leg.find('.//trias:TimedLeg/trias:LegBoard/trias:ServiceDeparture/trias:TimetabledTime', namespaces).text, "%Y-%m-%dT%H:%M:%SZ")).astimezone(pytz.timezone("Europe/Berlin")).strftime("%H:%M")
                        trip["departureEstimated"] = pytz.utc.localize(datetime.strptime(leg.find('.//trias:TimedLeg/trias:LegBoard/trias:ServiceDeparture/trias:EstimatedTime', namespaces).text, "%Y-%m-%dT%H:%M:%SZ")).astimezone(pytz.timezone("Europe/Berlin")).strftime("%H:%M")
                        trip["departureDelay"] = int((datetime.strptime(trip["departureEstimated"], "%H:%M") - datetime.strptime(trip["departureTimeTable"], "%H:%M")).total_seconds() // 60)
                        trip["startPlatform"] = leg.find('.//trias:TimedLeg/trias:LegBoard/trias:PlannedBay/trias:Text', namespaces).text
                        trip["line"] = leg.find('.//trias:TimedLeg/trias:Service/trias:ServiceSection/trias:PublishedLineName/trias:Text', namespaces).text
                    elif leg.find('.//trias:LegId', namespaces).text == str(trip["interchanges"] + 1):
                        trip["endLocation"] = leg.find('.//trias:TimedLeg/trias:LegAlight/trias:StopPointName/trias:Text', namespaces).text
                        trip["arrival"] = pytz.utc.localize(datetime.strptime(leg.find('.//trias:TimedLeg/trias:LegAlight/trias:ServiceArrival/trias:TimetabledTime', namespaces).text, "%Y-%m-%dT%H:%M:%SZ")).astimezone(pytz.timezone("Europe/Berlin")).strftime("%H:%M")
                        trip["endPlatform"] = leg.find('.//trias:TimedLeg/trias:LegAlight/trias:PlannedBay/trias:Text', namespaces).text
 
                trips.append(trip)
        
        return trips
    else:
        print("❌ Error fetching data")
        print("Status Code:", response.status_code)
        return None
    
def checkTrainDisruptions(startRef: str, stopRef: str, time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")):
    """
    Check for train disruptions.
    """
    template = loadTemplate("xml_templates/trip_request.xml")
    xml_request = fillTemplate(template, {
        "timestamp": time,
        "requestor_ref": REQUESTOR_REF,
        "start_ref": startRef,
        "stop_ref": stopRef,
    })

    headers = {
        "Content-Type": "text/xml"
    }

    # Send request
    response = requests.post(TRIAS_URL, data=xml_request.encode("utf-8"), headers=headers)
    response.encoding = 'utf-8'

    # Process response
    if response.status_code == 200:
        # Parse the XML
        root = ET.fromstring(response.text)
        # Find all Disruption elements
        situations = root.findall('.//trias:PtSituation', namespaces)

        if situations is None:
            return False
        else:
            for index, situation in enumerate(situations):
                priority = situation.find('.//siri:Priority', namespaces).text
                if priority is not None:
                    if int(priority) > 0 and int(priority) < 3:
                        summary = situation.find('.//siri:Summary', namespaces).text
                        description = situation.find('.//siri:Description', namespaces).text
                        detail = situation.find('.//siri:Detail', namespaces).text
                        print(int(priority))
                        print(summary)
                        print(description)
                        print(detail)
            return True
    else:
        print("❌ Error fetching data")
        print("Status Code:", response.status_code)
        return None