"""
Configuration settings for PyVVS.
"""

# VVS TRIAS API Configuration
vvsApiBaseUrl = "https://efastatic.vvs.de/unistuttgart/trias"
vvsApiVersion = "1.2"

# Default request parameters
defaultHeaders = {
    "Content-Type": "application/xml; charset=utf-8",
    "User-Agent": "PyVVS/0.1.0"
}

# Request timeouts (in seconds)
requestTimeout = 30
connectionTimeout = 10

# Default search parameters
defaultMaxResults = 20
defaultDepartureMonitorLimit = 50

# Time formats
timeFormat = "%Y-%m-%dT%H:%M:%S"
displayTimeFormat = "%H:%M"
dateFormat = "%Y-%m-%d"