"""
Core API client for VVS TRIAS interface.

Handles HTTP requests, XML template loading, and raw API communication.
"""

import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from config import (
    vvsApiBaseUrl, 
    defaultHeaders, 
    requestTimeout,
    timeFormat
)


class VVSApiClient:
    """Low-level API client for VVS TRIAS interface."""
    
    def __init__(self, apiUrl: str = vvsApiBaseUrl):
        """
        Initialize the API client.
        
        Args:
            apiUrl: The VVS API endpoint URL
        """
        self.apiUrl = apiUrl
        self.session = requests.Session()
        self.session.headers.update(defaultHeaders)
        
        # Get the directory where XML templates are stored
        self.templatesDir = Path(__file__).parent / "xml_templates"
    
    def _loadTemplate(self, templateName: str) -> str:
        """
        Load an XML template from the xml_templates directory.
        
        Args:
            templateName: Name of the template file (without .xml extension)
            
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        templatePath = self.templatesDir / f"{templateName}.xml"
        
        if not templatePath.exists():
            raise FileNotFoundError(f"Template not found: {templatePath}")
        
        with open(templatePath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _fillTemplate(self, template: str, **kwargs: Any) -> str:
        """
        Fill template placeholders with provided values.
        
        Args:
            template: Template string with {{placeholder}} format
            **kwargs: Values to substitute in template
            
        Returns:
            Filled template string
        """
        # Add default values
        defaults = {
            'timestamp': datetime.now().strftime(timeFormat),
            'requestorRef': 'uni0719'
        }
        
        # Merge defaults with provided kwargs
        values = {**defaults, **kwargs}
        
        # Replace template placeholders
        filledTemplate = template
        for key, value in values.items():
            placeholder = f"{{{{{key}}}}}"
            filledTemplate = filledTemplate.replace(placeholder, str(value))
        
        return filledTemplate
    
    def _makeRequest(self, xmlBody: str) -> requests.Response:
        """
        Make HTTP POST request to VVS API.
        
        Args:
            xmlBody: XML request body
            
        Returns:
            HTTP response object
            
        Raises:
            requests.RequestException: If request fails
        """
        try:
            response = self.session.post(
                self.apiUrl,
                data=xmlBody.encode('utf-8'),
                timeout=requestTimeout
            )
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            raise requests.RequestException(f"VVS API request failed: {e}")
    
    def findStops(self, location: str) -> str:
        """
        Search for stops by location name.
        
        Args:
            location: Location name to search for
            
        Returns:
            Raw XML response as string
        """
        template = self._loadTemplate("find_stops")
        xmlRequest = self._fillTemplate(template, location=location)
        
        response = self._makeRequest(xmlRequest)
        return response.text
    
    def getDepartures(
        self, 
        stopPointRef: str, 
        departureTime: Optional[str] = datetime.now().strftime(timeFormat),
        numberOfResults: int = 40
    ) -> str:
        """
        Get departures for a specific stop.
        
        Args:
            stopPointRef: Stop reference ID (e.g., 'de:08111:6008')
            departureTime: ISO format departure time (defaults to now)
            numberOfResults: Maximum number of results
            
        Returns:
            Raw XML response as string
        """
        
        template = self._loadTemplate("departures")
        xmlRequest = self._fillTemplate(
            template,
            stopPointRef=stopPointRef,
            departureTime=departureTime,
            numberOfResults=numberOfResults
        )
        response = self._makeRequest(xmlRequest)
        return response.text
    
    def getTripConnections(
        self,
        startRef: str,
        destinationRef: str,
        departureTime: Optional[str] = None,
        numberOfResults: int = 5,
        includeIntermediateStops: bool = False
    ) -> str:
        """
        Get trip connections between two stops.
        
        Args:
            startRef: Origin stop reference ID
            destinationRef: Destination stop reference ID
            departureTime: ISO format departure time (defaults to now)
            numberOfResults: Maximum number of connections
            includeIntermediateStops: Whether to include intermediate stops
            
        Returns:
            Raw XML response as string
        """
        if departureTime is None:
            departureTime = datetime.now().strftime(timeFormat)
        
        template = self._loadTemplate("trip_connections")
        xmlRequest = self._fillTemplate(
            template,
            startRef=startRef,
            destinationRef=destinationRef,
            departureTime=departureTime,
            numberOfResults=numberOfResults,
            includeIntermediateStops=str(includeIntermediateStops).lower()
        )
        
        response = self._makeRequest(xmlRequest)
        return response.text
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()