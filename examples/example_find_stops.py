#!/usr/bin/env python3
"""
Simple example: How to find stops/stations using PyVVS

This example shows how to search for public transport stops by name.
"""

import sys
import os
# Add parent directory to path so we can import pyvvs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import findStops, getStopByName

def main():
    print("=== PyVVS Example: Finding Stops ===\n")
    
    # Example 1: Search for stops by name
    print("1. Searching for 'Universität'...")
    stops = findStops("Universität")
    
    print(f"Found {len(stops)} stops:")
    for i, stop in enumerate(stops[:5], 1):  # Show first 5 results
        print(f"  {i}. {stop.name}")
        print(f"     ID: {stop.id}")
        if stop.locality:
            print(f"     City: {stop.locality}")
        if stop.latitude and stop.longitude:
            print(f"     Coordinates: {stop.latitude:.4f}, {stop.longitude:.4f}")
        print()

if __name__ == "__main__":
    main()