import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom
from datetime import datetime
from typing import List, Tuple, Optional, Dict
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


def load_template(file_path: str) -> str:
    """
    Load an XML template from file.
    
    Args:
        file_path (str): Path to the template file.
        
    Returns:
        str: The template content.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def fill_template(template: str, values: dict) -> str:
    """
    Fill template placeholders with actual values.
    
    Args:
        template (str): The template string with placeholders.
        values (dict): Dictionary of placeholder keys and values.
        
    Returns:
        str: The filled template.
    """
    for key, val in values.items():
        template = template.replace(f"{{{{{key}}}}}", val)
    return template

def convert_iso_duration(duration: str) -> str:
    """
    Convert ISO duration to a human-readable format.
    
    Args:
        duration (str): The ISO duration string to convert.
        
    Returns:
        str: The converted duration string.
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
    
    return duration  # Return original if parsing fails

def convert_utc_to_local(utc_time_str: str, format_str: str = "%Y-%m-%dT%H:%M:%SZ") -> datetime:
    """
    Convert UTC time string to local Berlin time.
    
    Args:
        utc_time_str (str): UTC time string.
        format_str (str): Format of the input time string.
        
    Returns:
        datetime: Local Berlin time.
    """
    utc_time = datetime.strptime(utc_time_str, format_str)
    local_time = pytz.utc.localize(utc_time).astimezone(pytz.timezone("Europe/Berlin"))
    return local_time

def find_stops(name: str) -> Optional[List[Tuple[str, str, str]]]:
    """
    Find stop information by name.
    
    Args:
        name (str): The string to search for the stop name.
        
    Returns:
        Optional[List[Tuple[str, str, str]]]: A list of triples (stop name, location name, stop point reference) if found, otherwise None.
    """
    template = load_template("xml_templates/locationInformation_request.xml")
    xml_request = fill_template(template, {
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

        stop_names_and_ids = []

        for element in elements:
            # Get all stop point names
            stop_point_names = element.findall('.//trias:StopPointName/trias:Text', namespaces)

            if stop_point_names is not None:
                locations = element.findall('.//trias:LocationName/trias:Text', namespaces)
                stop_point_refs = element.findall('.//trias:StopPointRef', namespaces)
                for index, stop in enumerate(stop_point_names):
                    stop_names_and_ids.append((stop.text, locations[index].text, stop_point_refs[index].text))
        
        return stop_names_and_ids
    else:
        print("❌ Error fetching data")
        print("Status Code:", response.status_code)
        return None

def request_trip(start_ref: str, stop_ref: str, time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")) -> Optional[List[Dict[str, str]]]:
    """
    Request trip information from start to destination.
    
    Args:
        start_ref (str): The start reference.
        stop_ref (str): The stop reference.
        time (str): Departure time. Defaults to current time.
        
    Returns:
        Optional[List[Dict[str, str]]]: A list of trip information dictionaries if successful, otherwise None.
    """
    template = load_template("xml_templates/trip_request.xml")
    xml_request = fill_template(template, {
        "timestamp": time,
        "requestor_ref": REQUESTOR_REF,
        "start_ref": start_ref,
        "stop_ref": stop_ref,
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
        trip_results = root.findall('.//trias:TripResult', namespaces)
        trips = []

        if trip_results is None:
            print("❌ No trip results found")
            return None
        else:
            for index, result in enumerate(trip_results):
                trip = {}
                duration_element = result.find('.//trias:Trip/trias:Duration', namespaces)
                if duration_element is not None:
                    trip["duration"] = convert_iso_duration(duration_element.text)
                
                interchanges_element = result.find('.//trias:Trip/trias:Interchanges', namespaces)
                trip["interchanges"] = int(interchanges_element.text if interchanges_element is not None else 0)

                for leg in result.findall('.//trias:Trip/trias:TripLeg', namespaces):
                    leg_id_element = leg.find('.//trias:LegId', namespaces)
                    if leg_id_element is not None and leg_id_element.text == "1":
                        start_location_element = leg.find('.//trias:TimedLeg/trias:LegBoard/trias:StopPointName/trias:Text', namespaces)
                        if start_location_element is not None:
                            trip["startLocation"] = start_location_element.text
                        
                        departure_timetabled_element = leg.find('.//trias:TimedLeg/trias:LegBoard/trias:ServiceDeparture/trias:TimetabledTime', namespaces)
                        if departure_timetabled_element is not None:
                            local_time = convert_utc_to_local(departure_timetabled_element.text)
                            trip["departureTimeTable"] = local_time.strftime("%H:%M")
                        
                        departure_estimated_element = leg.find('.//trias:TimedLeg/trias:LegBoard/trias:ServiceDeparture/trias:EstimatedTime', namespaces)
                        if departure_estimated_element is not None:
                            local_time = convert_utc_to_local(departure_estimated_element.text)
                            trip["departureEstimated"] = local_time.strftime("%H:%M")
                            
                            # Calculate delay
                            if "departureTimeTable" in trip:
                                scheduled = datetime.strptime(trip["departureTimeTable"], "%H:%M")
                                estimated = datetime.strptime(trip["departureEstimated"], "%H:%M")
                                trip["departureDelay"] = int((estimated - scheduled).total_seconds() // 60)
                        
                        start_platform_element = leg.find('.//trias:TimedLeg/trias:LegBoard/trias:PlannedBay/trias:Text', namespaces)
                        if start_platform_element is not None:
                            trip["startPlatform"] = start_platform_element.text
                        
                        line_element = leg.find('.//trias:TimedLeg/trias:Service/trias:ServiceSection/trias:PublishedLineName/trias:Text', namespaces)
                        if line_element is not None:
                            trip["line"] = line_element.text
                            
                    elif leg_id_element is not None and leg_id_element.text == str(trip["interchanges"] + 1):
                        end_location_element = leg.find('.//trias:TimedLeg/trias:LegAlight/trias:StopPointName/trias:Text', namespaces)
                        if end_location_element is not None:
                            trip["endLocation"] = end_location_element.text
                        
                        arrival_element = leg.find('.//trias:TimedLeg/trias:LegAlight/trias:ServiceArrival/trias:TimetabledTime', namespaces)
                        if arrival_element is not None:
                            local_time = convert_utc_to_local(arrival_element.text)
                            trip["arrival"] = local_time.strftime("%H:%M")
                        
                        end_platform_element = leg.find('.//trias:TimedLeg/trias:LegAlight/trias:PlannedBay/trias:Text', namespaces)
                        if end_platform_element is not None:
                            trip["endPlatform"] = end_platform_element.text

                trips.append(trip)
        
        return trips
    else:
        print("❌ Error fetching data")
        print("Status Code:", response.status_code)
        return None

def check_train_disruptions(start_ref: str, stop_ref: str, time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")):
    """
    Check for train disruptions on the route.
    
    Args:
        start_ref (str): The start reference.
        stop_ref (str): The stop reference.
        time (str): Departure time. Defaults to current time.
        
    Returns:
        Optional[bool]: True if disruptions found, False if none, None on error.
    """
    template = load_template("xml_templates/trip_request.xml")
    xml_request = fill_template(template, {
        "timestamp": time,
        "requestor_ref": REQUESTOR_REF,
        "start_ref": start_ref,
        "stop_ref": stop_ref,
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
                priority_element = situation.find('.//siri:Priority', namespaces)
                if priority_element is not None:
                    priority = int(priority_element.text)
                    if 0 < priority < 3:
                        summary_element = situation.find('.//siri:Summary', namespaces)
                        description_element = situation.find('.//siri:Description', namespaces)
                        detail_element = situation.find('.//siri:Detail', namespaces)
                        
                        print(priority)
                        if summary_element is not None:
                            print(summary_element.text)
                        if description_element is not None:
                            print(description_element.text)
                        if detail_element is not None:
                            print(detail_element.text)
            return True
    else:
        print("❌ Error fetching data")
        print("Status Code:", response.status_code)
        return None