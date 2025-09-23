"""
High-level user-friendly functions for PyVVS.

Provides easy-to-use functions that combine API calls with parsing to return Python objects.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from api import VVSApiClient
from parsers import VVSResponseParser
from models import Stop, Departure, Connection


def findStops(location: str) -> List[Stop]:
    """
    Find stops by location name.
    
    Args:
        location: Location name to search for (e.g., "Hauptbahnhof", "Marienplatz")
        
    Returns:
        List of Stop objects matching the search query
        
    Example:
        >>> stops = findStops("Hauptbahnhof Stuttgart")
        >>> for stop in stops:
        ...     print(f"{stop.name} ({stop.id})")
    """
    with VVSApiClient() as client:
        xmlResponse = client.findStops(location)
        return VVSResponseParser.parseStops(xmlResponse)


def listDepartures(
    stopId: str, 
    departureTime: Optional[datetime] = datetime.now(),
    numberOfResults: int = 40
) -> List[Departure]:
    """
    Get departure information for a specific stop.
    
    Args:
        stopId: Stop reference ID (e.g., 'de:08111:6008')
        departureTime: Desired departure time as a datetime object (defaults to now)
        numberOfResults: Maximum number of departures to return
        
    Returns:
        List of Departure objects
    """
    departureTimeStr = departureTime.strftime("%Y-%m-%dT%H:%M:%S")
    
    with VVSApiClient() as client:
        xmlResponse = client.getDepartures(
            stopPointRef=stopId,
            departureTime=departureTimeStr,
            numberOfResults=numberOfResults
        )
        return VVSResponseParser.parseDepartures(xmlResponse)


def listConnections(
    originId: str,
    destinationId: str,
    departureTime: Optional[datetime] = None,
    numberOfResults: int = 5,
    includeIntermediateStops: bool = False
) -> List[Connection]:
    """
    Get trip connections between two stops.
    
    Args:
        originId: Origin stop reference ID
        destinationId: Destination stop reference ID  
        departureTime: Desired departure time (defaults to now)
        numberOfResults: Maximum number of connections to return
        includeIntermediateStops: Whether to include intermediate stops in legs
        
    Returns:
        List of Connection objects
        
    Example:
        >>> connections = listConnections("de:08111:6008", "de:08111:1234")
        >>> for conn in connections:
        ...     print(f"{conn.origin.name} → {conn.destination.name}")
        ...     print(f"Duration: {conn.durationText}")
        ...     for leg in conn.legs:
        ...         print(f"  {leg}")
    """
    if departureTime is None:
        departureTime = datetime.now()
    
    departureTimeStr = departureTime.strftime("%Y-%m-%dT%H:%M:%S")
    
    with VVSApiClient() as client:
        xmlResponse = client.getTripConnections(
            startRef=originId,
            destinationRef=destinationId,
            departureTime=departureTimeStr,
            numberOfResults=numberOfResults,
            includeIntermediateStops=includeIntermediateStops
        )
        # Save XML response to a human-readable (pretty-printed) XML file
        import xml.dom.minidom

        dom = xml.dom.minidom.parseString(xmlResponse)
        pretty_xml = dom.toprettyxml(indent="  ")

        with open("trip_connections.xml", "w", encoding="utf-8") as f:
            f.write(pretty_xml)
        return VVSResponseParser.parseConnections(xmlResponse)