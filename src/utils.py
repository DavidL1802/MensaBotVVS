import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Tuple, Optional

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
        print("✅ Successful! Formatted XML response:\n")
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
                for index, name in enumerate(stopPointNames):
                    stopNamesAndIDs.append((name.text, locations[index].text, stopPointRefs[index].text))
        
        return stopNamesAndIDs
    else:
        print("❌ Error fetching data")
        print("Status Code:", response.status_code)
        return None
    
def requestTrip(startRef: str, stopRef: str) -> Optional[List[Tuple[str, str, str]]]:
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
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "requestor_ref": REQUESTOR_REF,
        "start_ref": startRef
    })

    headers = {
        "Content-Type": "text/xml"
    }

    # Send request
    response = requests.post(TRIAS_URL, data=xml_request.encode("utf-8"), headers=headers)
    response.encoding = 'utf-8'

    # Process response
    if response.status_code == 200:
        print("✅ Successful! Formatted XML response:\n")
        # Parse the XML
        root = ET.fromstring(response.text)

        # Find all Trip elements
        elements = root.findall('.//trias:Trip', namespaces)

        tripInfo = []

        for element in elements:
            # Get all trip names
            tripNames = element.findall('.//trias:TripName/trias:Text', namespaces)

            if tripNames is not None:
                locations = element.findall('.//trias:LocationName/trias:Text', namespaces)
                stopPointRefs = element.findall('.//trias:StopPointRef', namespaces)
                for index, name in enumerate(tripNames):
                    tripInfo.append((name.text, locations[index].text, stopPointRefs[index].text))
        
        return tripInfo
    else:
        print("❌ Error fetching data")
        print("Status Code:", response.status_code)
        return None