import requests
import xml.etree.ElementTree as ET
import xml.dom.minidom
from datetime import datetime
from typing import List, Dict, Optional
import pytz
from utils import fill_template, convert_utc_to_local

class Departure:
    """
    A class to handle departure requests for VVS transportation data.
    """
    
    # Embedded XML template for departure requests
    DEPARTURE_REQUEST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
    <Trias version="1.2" xmlns="http://www.vdv.de/trias" xmlns:siri="http://www.siri.org.uk/siri">
        <ServiceRequest>
            <siri:RequestTimestamp>{{timestamp}}</siri:RequestTimestamp>
            <siri:RequestorRef>{{requestor_ref}}</siri:RequestorRef>
            <RequestPayload>
                <StopEventRequest>
                    <Location>
                        <LocationRef>
                            <StopPointRef>{{stop_point_ref}}</StopPointRef>	
                        </LocationRef>
                        <DepArrTime>{{departure_time}}</DepArrTime>
                    </Location>
                    <Params>
                        <NumberOfResults>{{number_of_results}}</NumberOfResults>
                        <StopEventType>departure</StopEventType>
                        <PtModeFilter>
                            <Exclude>false</Exclude>
                            <RailSubmode>suburbanRailway</RailSubmode>
                        </PtModeFilter>
                        <IncludeRealtimeData>true</IncludeRealtimeData>
                    </Params>
                </StopEventRequest>
            </RequestPayload>
        </ServiceRequest>
    </Trias>"""
    
    def __init__(self, stop_point_ref: str, departure_time: Optional[str] = None, number_of_results: int = 40):
        """
        Initialize a Departure instance.
        
        Args:
            stop_point_ref (str): The stop point reference ID (e.g., 'de:08111:6008')
            departure_time (Optional[str]): The departure time in ISO format. Defaults to current time.
            number_of_results (int): Number of departure results to fetch. Defaults to 40.
        """
        self.stop_point_ref = stop_point_ref
        self.departure_time = departure_time or datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.number_of_results = number_of_results
        self.trias_url = "https://efastatic.vvs.de/unistuttgart/trias"
        self.requestor_ref = "uni0719"
        
        # XML namespaces
        self.namespaces = {
            'trias': 'http://www.vdv.de/trias',
            'siri': 'http://www.siri.org.uk/siri',
            'acsb': 'http://www.ifopt.org.uk/acsb',
            'ifopt': 'http://www.ifopt.org.uk/ifopt',
            'datex2': 'http://datex2.eu/schema/1_0/1_0'
        }
    
    def get_departures(self) -> Optional[List[Dict[str, str]]]:
        """
        Fetch departure information for the specified stop.
        
        Returns:
            Optional[List[Dict[str, str]]]: A list of departure dictionaries if successful, None otherwise.
        """
        try:
            # Use the embedded XML template
            xml_request = fill_template(self.DEPARTURE_REQUEST_TEMPLATE, {
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "requestor_ref": self.requestor_ref,
                "stop_point_ref": self.stop_point_ref,
                "departure_time": self.departure_time,
                "number_of_results": str(self.number_of_results),
            })
            
            headers = {
                "Content-Type": "text/xml"
            }
            
            # Send request
            response = requests.post(self.trias_url, data=xml_request.encode("utf-8"), headers=headers)
            response.encoding = 'utf-8'
            
            if response and response.status_code == 200:
                return self._parse_departure_response(response.text)
            else:
                print(f"❌ Error fetching departure data. Status Code: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            print(f"❌ Error in get_departures: {str(e)}")
            return None
    
    def _parse_departure_response(self, response_text: str) -> List[Dict[str, str]]:
        """
        Parse the XML response and extract departure information.
        
        Args:
            response_text (str): The XML response text from the API.
            
        Returns:
            List[Dict[str, str]]: A list of departure information dictionaries.
        """
        departures = []
        
        try:
            # Parse the XML
            root = ET.fromstring(response_text)
            
            # Find all StopEvent elements (departures)
            stop_events = root.findall('.//trias:StopEvent', self.namespaces)
            
            for event in stop_events:
                departure = {}
                
                # Extract basic information
                stop_point_name = event.find('.//trias:ThisCall/trias:CallAtStop/trias:StopPointName/trias:Text', self.namespaces)
                if stop_point_name is not None:
                    departure["stop_name"] = stop_point_name.text
                
                # Extract service information
                service_section = event.find('.//trias:Service', self.namespaces)
                if service_section is not None:
                    line_name = service_section.find('.//trias:ServiceSection/trias:PublishedLineName/trias:Text', self.namespaces)
                    if line_name is not None:
                        departure["line"] = line_name.text
                    
                    destination = service_section.find('.//trias:DestinationText/trias:Text', self.namespaces)
                    if destination is not None:
                        departure["destination"] = destination.text
                    
                    # Extract JourneyRef
                    journey_ref = service_section.find('.//trias:JourneyRef', self.namespaces)
                    if journey_ref is not None:
                        departure["journey_ref"] = journey_ref.text
                
                # Extract timing information
                timetabled_time = event.find('.//trias:ThisCall/trias:CallAtStop/trias:ServiceDeparture/trias:TimetabledTime', self.namespaces)
                if timetabled_time is not None:
                    # Convert UTC to local time
                    local_time = convert_utc_to_local(timetabled_time.text)
                    departure["scheduled_time"] = local_time.strftime("%H:%M")
                
                estimated_time = event.find('.//trias:ThisCall/trias:CallAtStop/trias:ServiceDeparture/trias:EstimatedTime', self.namespaces)
                if estimated_time is not None:
                    # Convert UTC to local time
                    local_time = convert_utc_to_local(estimated_time.text)
                    departure["estimated_time"] = local_time.strftime("%H:%M")
                    
                    # Calculate delay
                    if "scheduled_time" in departure:
                        scheduled = datetime.strptime(departure["scheduled_time"], "%H:%M")
                        estimated = datetime.strptime(departure["estimated_time"], "%H:%M")
                        delay_minutes = int((estimated - scheduled).total_seconds() // 60)
                        departure["delay"] = delay_minutes
                
                # Extract platform information
                planned_bay = event.find('.//trias:ThisCall/trias:CallAtStop/trias:PlannedBay/trias:Text', self.namespaces)
                if planned_bay is not None:
                    departure["platform"] = planned_bay.text
                
                # Only add if we have essential information
                if "line" in departure and "scheduled_time" in departure:
                    departures.append(departure)
            
        except Exception as e:
            print(f"❌ Error parsing departure response: {str(e)}")
        
        return departures
    
    def print_departures(self) -> None:
        """
        Fetch and print departure information in a readable format.
        """
        departures = self.get_departures()
        
        if not departures:
            print("❌ No departures found or error occurred.")
            return
        
        print(f"🚌 Departures from {departures[0].get('stop_name', 'Unknown Stop')}:")
        print("-" * 120)
        
        for departure in departures:
            line = departure.get("line", "Unknown")
            destination = departure.get("destination", "Unknown Destination")
            scheduled = departure.get("scheduled_time", "Unknown")
            estimated = departure.get("estimated_time", scheduled)
            delay = departure.get("delay", 0)
            platform = departure.get("platform", "Unknown")
            journey_ref = departure.get("journey_ref", "Unknown")
            
            delay_str = f" (+{delay} min)" if delay > 0 else f" ({delay} min)" if delay < 0 else ""
            
            print(f"{line:8} → {destination:30} | {scheduled} → {estimated}{delay_str:12} | Platform: {platform:10} | JourneyRef: {journey_ref}")
    
    def save_response_debug(self, filename: str = "departure_response.xml") -> None:
        """
        Save the raw XML response for debugging purposes.
        
        Args:
            filename (str): The filename to save the response to.
        """
        try:
            xml_request = fill_template(self.DEPARTURE_REQUEST_TEMPLATE, {
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "requestor_ref": self.requestor_ref,
                "stop_point_ref": self.stop_point_ref,
                "departure_time": self.departure_time,
                "number_of_results": str(self.number_of_results),
            })
            
            headers = {
                "Content-Type": "text/xml"
            }
            
            response = requests.post(self.trias_url, data=xml_request.encode("utf-8"), headers=headers)
            response.encoding = 'utf-8'
            
            if response and response.status_code == 200:
                # Pretty print the XML
                try:
                    dom = xml.dom.minidom.parseString(response.text)
                    pretty_response = dom.toprettyxml(indent="  ")
                except Exception:
                    pretty_response = response.text  # fallback to raw
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(pretty_response)
                print(f"✅ Response saved to {filename}")
            else:
                print(f"❌ Error fetching data. Status Code: {response.status_code if response else 'No response'}")
                
        except Exception as e:
            print(f"❌ Error saving response: {str(e)}")