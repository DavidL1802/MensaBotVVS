"""
Data models for PyVVS.

Contains dataclasses representing VVS transport entities like stops, departures, and connections.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
import pytz

# Timezone for Stuttgart
STUTTGART_TZ = pytz.timezone('Europe/Berlin')


class TransportMode(Enum):
    """Transport mode enumeration."""
    RAIL = "rail"
    BUS = "bus"
    TRAM = "tram"
    SUBWAY = "subway"
    UNKNOWN = "unknown"


class StopType(Enum):
    """Stop type enumeration."""
    STOP = "stop"
    PLATFORM = "platform"
    STATION = "station"
    UNKNOWN = "unknown"


@dataclass
class Stop:
    """Represents a public transport stop or station."""
    
    id: str
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    locality: Optional[str] = None
    stopType: StopType = StopType.UNKNOWN
    
    def __str__(self) -> str:
        location = f" ({self.locality})" if self.locality else ""
        return f"{self.name}{location}"


@dataclass 
class Departure:
    """Represents a departure from a stop."""
    
    journeyRef: str
    line: str
    destination: str
    scheduledTime: str  # Formatted time string (H:M)
    scheduledDateTime: Optional[datetime] = None  # Internal datetime for calculations
    estimatedTime: Optional[datetime] = None
    delayMinutes: Optional[int] = None
    platform: Optional[str] = None
    transportMode: TransportMode = TransportMode.UNKNOWN
    realtime: bool = False
    
    @property
    def delayText(self) -> str:
        """Return human-readable delay information."""
        if self.delayMinutes is None:
            return "on time"
        elif self.delayMinutes == 0:
            return "on time"
        else:
            return f"{self.delayMinutes} min late"
    
    @property
    def displayTime(self) -> str:
        """Return time for display (estimated if available, otherwise scheduled)."""
        if self.estimatedTime:
            # Convert estimated time to Stuttgart timezone if timezone-aware
            timeToShow = self.estimatedTime
            if timeToShow.tzinfo is not None:
                timeToShow = timeToShow.astimezone(STUTTGART_TZ)
            return timeToShow.strftime("%H:%M")
        else:
            # Return the already formatted scheduled time
            return self.scheduledTime
    
    def __str__(self) -> str:
        return f"{self.line} → {self.destination} ({self.displayTime}, {self.delayText})"


@dataclass
class Connection:
    """Represents a trip connection between two stops."""
    
    origin: Stop
    destination: Stop
    departureTime: datetime
    arrivalTime: datetime
    durationMinutes: int
    legs: List['ConnectionLeg']
    
    @property
    def durationText(self) -> str:
        """Return human-readable duration."""
        hours = self.durationMinutes // 60
        minutes = self.durationMinutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}min"
        else:
            return f"{minutes}min"
    
    def __str__(self) -> str:
        return f"{self.origin.name} → {self.destination.name} ({self.durationText})"


@dataclass
class ConnectionLeg:
    """Represents one leg of a journey connection."""
    
    origin: Stop
    destination: Stop
    departureTime: datetime
    arrivalTime: datetime
    line: Optional[str] = None
    transportMode: TransportMode = TransportMode.UNKNOWN
    intermediateStops: List[Stop] = None
    
    def __post_init__(self):
        if self.intermediateStops is None:
            self.intermediateStops = []
    
    @property
    def isWalking(self) -> bool:
        """Check if this leg is a walking segment."""
        return self.line is None
    
    def __str__(self) -> str:
        if self.isWalking:
            return f"Walk from {self.origin.name} to {self.destination.name}"
        else:
            return f"{self.line} from {self.origin.name} to {self.destination.name}"


@dataclass
class DepartureStatistic:
    """Represents a departure statistic entry for database storage."""
    
    journeyRef: str
    timestamp: datetime
    line: str
    delayMinutes: Optional[int]
    scheduledTime: datetime
    stopId: str
    
    def toDict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            'journeyRef': self.journeyRef,
            'timestamp': self.timestamp.isoformat(),
            'line': self.line,
            'delayMinutes': self.delayMinutes,
            'scheduledTime': self.scheduledTime.isoformat(),
            'stopId': self.stopId
        }
    
    @classmethod
    def fromDeparture(cls, departure: Departure, stopId: str) -> 'DepartureStatistic':
        """Create a statistic entry from a Departure object."""
        return cls(
            journeyRef=departure.journeyRef,
            timestamp=datetime.now(),
            line=departure.line,
            delayMinutes=departure.delayMinutes,
            scheduledTime=departure.scheduledTime,
            stopId=stopId
        )