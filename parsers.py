"""
XML response parsers for VVS TRIAS API.

Converts raw XML responses into Python objects using the models module.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional, Dict, Any
import pytz

from models import Stop, Departure, Connection, ConnectionLeg, TransportMode, StopType


# VVS TRIAS XML namespaces
NAMESPACES = {
    'trias': 'http://www.vdv.de/trias',
    'siri': 'http://www.siri.org.uk/siri'
}

# Timezone for Stuttgart
STUTTGART_TZ = pytz.timezone('Europe/Berlin')


def _parseDateTime(datetimeStr: str) -> Optional[datetime]:
    """
    Parse ISO datetime string from VVS API to local Stuttgart time.
    
    VVS API always returns UTC time in format: 2025-09-23T12:34:00Z
    This function converts it to Stuttgart local time.
    
    Args:
        datetimeStr: ISO format datetime string from VVS API
        
    Returns:
        Datetime object in Stuttgart timezone or None if parsing fails
    """
    if not datetimeStr:
        return None
        
    try:
        # VVS API returns UTC time with Z suffix
        if datetimeStr.endswith('Z'):
            # Remove Z and parse as UTC
            utc_dt = datetime.strptime(datetimeStr[:-1], "%Y-%m-%dT%H:%M:%S")
            utc_dt = pytz.UTC.localize(utc_dt)
            # Convert to Stuttgart local time
            return utc_dt.astimezone(STUTTGART_TZ)
        
        # Fallback: try parsing without Z (assume UTC)
        utc_dt = datetime.strptime(datetimeStr, "%Y-%m-%dT%H:%M:%S")
        utc_dt = pytz.UTC.localize(utc_dt)
        return utc_dt.astimezone(STUTTGART_TZ)
        
    except (ValueError, TypeError):
        return None


def _parseTimeString(datetimeStr: str) -> Optional[str]:
    """
    Parse ISO datetime string from VVS API and return as H:M format.
    
    Args:
        datetimeStr: ISO format datetime string from VVS API
        
    Returns:
        Time string in H:M format or None if parsing fails
    """
    dt = _parseDateTime(datetimeStr)
    return dt.strftime("%H:%M") if dt else None


def _getText(element: Optional[ET.Element], default: str = "") -> str:
    """Get text content from XML element safely."""
    return element.text if element is not None else default


def _parseTransportMode(modeText: str) -> TransportMode:
    """Parse transport mode from text."""
    modeLower = modeText.lower()
    
    if 'rail' in modeLower or 'sbahn' in modeLower or 'suburban' in modeLower:
        return TransportMode.RAIL
    elif 'bus' in modeLower:
        return TransportMode.BUS
    elif 'tram' in modeLower or 'stadtbahn' in modeLower:
        return TransportMode.TRAM
    elif 'subway' in modeLower or 'ubahn' in modeLower:
        return TransportMode.SUBWAY
    else:
        return TransportMode.UNKNOWN


class VVSResponseParser:
    """Parser for VVS TRIAS XML responses."""
    
    @staticmethod
    def parseStops(xmlResponse: str) -> List[Stop]:
        """
        Parse stop search response XML.
        
        Args:
            xmlResponse: Raw XML response from findStops API call
            
        Returns:
            List of Stop objects
        """
        stops = []
        
        try:
            root = ET.fromstring(xmlResponse)
            
            # Find all location results
            for location in root.findall('.//trias:Location', NAMESPACES):
                stopPoint = location.find('.//trias:StopPoint', NAMESPACES)
                if stopPoint is None:
                    continue
                
                # Extract stop information
                stopPointRef = _getText(stopPoint.find('.//trias:StopPointRef', NAMESPACES))
                stopPointName = _getText(stopPoint.find('.//trias:StopPointName/trias:Text', NAMESPACES))
                
                # Extract coordinates if available
                pos = location.find('.//trias:GeoPosition', NAMESPACES)
                latitude = longitude = None
                if pos is not None:
                    latElem = pos.find('trias:Latitude', NAMESPACES)
                    lonElem = pos.find('trias:Longitude', NAMESPACES) 
                    latitude = float(_getText(latElem)) if latElem is not None else None
                    longitude = float(_getText(lonElem)) if lonElem is not None else None
                
                # Extract locality
                localityElem = location.find('.//trias:LocationName/trias:Text', NAMESPACES)
                locality = _getText(localityElem) if localityElem is not None else None
                
                if stopPointRef and stopPointName:
                    stop = Stop(
                        id=stopPointRef,
                        name=stopPointName,
                        latitude=latitude,
                        longitude=longitude,
                        locality=locality,
                        stopType=StopType.STOP
                    )
                    stops.append(stop)
        
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse stops XML: {e}")
        
        return stops
    
    @staticmethod
    def parseDepartures(xmlResponse: str) -> List[Departure]:
        """
        Parse departure response XML.
        
        Args:
            xmlResponse: Raw XML response from getDepartures API call
            
        Returns:
            List of Departure objects
        """
        departures = []
        
        try:
            root = ET.fromstring(xmlResponse)
            
            # Find all stop events (departures)
            for stopEvent in root.findall('.//trias:StopEvent', NAMESPACES):
                # Extract journey reference
                journeyRefElem = stopEvent.find('.//trias:JourneyRef', NAMESPACES)
                journeyRef = _getText(journeyRefElem) if journeyRefElem is not None else ""
                
                # Extract service information
                service = stopEvent.find('.//trias:Service', NAMESPACES)
                line = ""
                destination = ""
                transportMode = TransportMode.UNKNOWN
                
                if service is not None:
                    lineElem = service.find('.//trias:PublishedLineName/trias:Text', NAMESPACES)
                    line = _getText(lineElem)
                    
                    destElem = service.find('.//trias:DestinationText/trias:Text', NAMESPACES)
                    destination = _getText(destElem)
                    
                    modeElem = service.find('.//trias:Mode', NAMESPACES)
                    if modeElem is not None:
                        modeName = _getText(modeElem.find('.//trias:Name/trias:Text', NAMESPACES))
                        transportMode = _parseTransportMode(modeName)
                
                # Extract timing information
                thisCall = stopEvent.find('trias:ThisCall', NAMESPACES)
                timetabledTimeElem = None
                estimatedTimeElem = None
                platform = None
                
                if thisCall is not None:
                    serviceDeparture = thisCall.find('.//trias:ServiceDeparture', NAMESPACES)
                    if serviceDeparture is not None:
                        timetabledTimeElem = serviceDeparture.find('trias:TimetabledTime', NAMESPACES)
                        estimatedTimeElem = serviceDeparture.find('trias:EstimatedTime', NAMESPACES)
                    
                    # Extract platform from PlannedBay
                    platformElem = thisCall.find('.//trias:PlannedBay/trias:Text', NAMESPACES)
                    platform = _getText(platformElem) if platformElem is not None else None

                scheduledDateTime = _parseDateTime(_getText(timetabledTimeElem)) if timetabledTimeElem is not None else None
                scheduledTime = _parseTimeString(_getText(timetabledTimeElem)) if timetabledTimeElem is not None else None
                estimatedTime = _parseDateTime(_getText(estimatedTimeElem)) if estimatedTimeElem is not None else None
                
                # Calculate delay
                delayMinutes = None
                realtime = estimatedTime is not None
                
                if scheduledDateTime and estimatedTime:
                    delaySeconds = (estimatedTime - scheduledDateTime).total_seconds()
                    delayMinutes = int(delaySeconds / 60)
                
                if journeyRef and line and destination and scheduledTime:
                    departure = Departure(
                        journeyRef=journeyRef,
                        line=line,
                        destination=destination,
                        scheduledTime=scheduledTime,
                        _scheduledDateTime=scheduledDateTime,
                        estimatedTime=estimatedTime,
                        delayMinutes=delayMinutes,
                        platform=platform,
                        transportMode=transportMode,
                        realtime=realtime
                    )
                    departures.append(departure)
        
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse departures XML: {e}")
        
        return departures
    
    @staticmethod
    def parseConnections(xmlResponse: str) -> List[Connection]:
        """
        Parse trip connections response XML.
        
        Args:
            xmlResponse: Raw XML response from getTripConnections API call
            
        Returns:
            List of Connection objects
        """
        connections = []
        
        try:
            root = ET.fromstring(xmlResponse)
            
            # Find all trip results
            for trip in root.findall('.//trias:Trip', NAMESPACES):
                # Extract basic trip information
                startTimeElem = trip.find('.//trias:StartTime', NAMESPACES)
                endTimeElem = trip.find('.//trias:EndTime', NAMESPACES)
                durationElem = trip.find('.//trias:Duration', NAMESPACES)
                
                if not all([startTimeElem, endTimeElem]):
                    continue
                
                departureTime = _parseDateTime(_getText(startTimeElem))
                arrivalTime = _parseDateTime(_getText(endTimeElem))
                
                if not departureTime or not arrivalTime:
                    continue
                
                # Calculate duration in minutes
                durationMinutes = int((arrivalTime - departureTime).total_seconds() / 60)
                
                # Parse legs
                legs = []
                for leg in trip.findall('.//trias:TripLeg', NAMESPACES):
                    legObj = VVSResponseParser._parseConnectionLeg(leg)
                    if legObj:
                        legs.append(legObj)
                
                if legs:
                    # Origin and destination from first and last leg
                    origin = legs[0].origin
                    destination = legs[-1].destination
                    
                    connection = Connection(
                        origin=origin,
                        destination=destination,
                        departureTime=departureTime,
                        arrivalTime=arrivalTime,
                        durationMinutes=durationMinutes,
                        legs=legs
                    )
                    connections.append(connection)
        
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse connections XML: {e}")
        
        return connections
    
    @staticmethod
    def _parseConnectionLeg(legElement: ET.Element) -> Optional[ConnectionLeg]:
        """Parse a single connection leg from XML element."""
        try:
            # Extract timing
            startTimeElem = legElement.find('.//trias:StartTime', NAMESPACES)
            endTimeElem = legElement.find('.//trias:EndTime', NAMESPACES)
            
            departureTime = _parseDateTime(_getText(startTimeElem)) if startTimeElem is not None else None
            arrivalTime = _parseDateTime(_getText(endTimeElem)) if endTimeElem is not None else None
            
            if not departureTime or not arrivalTime:
                return None
            
            # Extract origin and destination stops
            originElem = legElement.find('.//trias:LegStart/trias:StopPointRef', NAMESPACES)
            destElem = legElement.find('.//trias:LegEnd/trias:StopPointRef', NAMESPACES)
            
            originNameElem = legElement.find('.//trias:LegStart/trias:StopPointName/trias:Text', NAMESPACES)
            destNameElem = legElement.find('.//trias:LegEnd/trias:StopPointName/trias:Text', NAMESPACES)
            
            origin = Stop(
                id=_getText(originElem),
                name=_getText(originNameElem)
            ) if originElem is not None else None
            
            destination = Stop(
                id=_getText(destElem),
                name=_getText(destNameElem)
            ) if destElem is not None else None
            
            if not origin or not destination:
                return None
            
            # Extract line information (if it's not a walking leg)
            serviceElem = legElement.find('.//trias:Service', NAMESPACES)
            line = None
            transportMode = TransportMode.UNKNOWN
            
            if serviceElem is not None:
                lineElem = serviceElem.find('.//trias:PublishedLineName/trias:Text', NAMESPACES)
                line = _getText(lineElem) if lineElem is not None else None
                
                modeElem = serviceElem.find('.//trias:Mode', NAMESPACES)
                if modeElem is not None:
                    modeName = _getText(modeElem.find('.//trias:Name/trias:Text', NAMESPACES))
                    transportMode = _parseTransportMode(modeName)
            
            return ConnectionLeg(
                origin=origin,
                destination=destination,
                departureTime=departureTime,
                arrivalTime=arrivalTime,
                line=line,
                transportMode=transportMode
            )
        
        except Exception:
            return None