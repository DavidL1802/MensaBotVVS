#!/usr/bin/env python3
"""
Simple example: How to get departure times using PyVVS

This example shows how to get real-time departure information for a specific stop.
"""

import sys
import os
# Add parent directory to path so we can import pyvvs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import listDepartures

def main():
    print("=== PyVVS Example: Getting Departures ===\n")
    
    # Example 1: Get current departures
    print("1. Getting current departures...")
    stopId = "de:08111:6008" # Universität
    stopName = "Universität"
    departures = listDepartures(stopId, numberOfResults=10)

    for dep in departures:
        print(f"{stopName} - {dep.line} to {dep.destination} at {dep.scheduledTime} (+{dep.delayMinutes} min)")

if __name__ == "__main__":
    main()