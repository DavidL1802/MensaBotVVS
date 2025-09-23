#!/usr/bin/env python3
"""
Simple example: How to find route connections using PyVVS

This example shows how to plan trips and get route connections between two stops.
"""

import sys
import os
# Add parent directory to path so we can import pyvvs
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from tools import findStops, listConnections

def main():
    print("=== PyVVS Example: Finding Route Connections ===\n")

    originId = "de:08111:6008"  # Stuttgart Hauptbahnhof
    destId = "de:08111:2077"    # Stuttgart Flughafen
    originName = "Stuttgart Hauptbahnhof"
    destName = "Stuttgart Flughafen"
    
    print(f"\nPlanning trip from:")
    print(f"  Origin: {originName} (ID: {originId})")
    print(f"  Destination: {destName} (ID: {destId})")
    print()
    
    # Example 2: Get connections for now
    print("2. Getting connections for immediate departure...")
    connections = listConnections(originId, destId, numberOfResults=3)
    
    if not connections:
        print("No connections found!")
        return
    
    print(f"Found {len(connections)} connections:\n")
    
    for i, conn in enumerate(connections, 1):
        print(f"Connection {i}:")
        print(f"  Duration: {conn.duration_text}")
        print(f"  Departure: {conn.departure_time.strftime('%H:%M')}")
        print(f"  Arrival: {conn.arrival_time.strftime('%H:%M')}")
        print(f"  Transfers: {len(conn.legs) - 1}")
        print("  Route:")
        
        for j, leg in enumerate(conn.legs):
            transfer_info = " (transfer)" if j > 0 else ""
            print(f"    {j+1}. {leg.line}: {leg.origin.name} → {leg.destination.name}{transfer_info}")
            if leg.departure_time and leg.arrival_time:
                print(f"       {leg.departure_time.strftime('%H:%M')} - {leg.arrival_time.strftime('%H:%M')} ({leg.duration_text})")
        print()
    
    # Example 3: Get connections for a specific time
    futureTime = datetime.now() + timedelta(hours=2)
    print(f"3. Getting connections for departure at {futureTime.strftime('%H:%M')}...")
    
    futureConnections = listConnections(
        originId, 
        destId, 
        departureTime=futureTime,
        numberOfResults=2
    )
    
    print(f"Found {len(futureConnections)} connections for later:")
    for i, conn in enumerate(futureConnections, 1):
        print(f"  {i}. {conn.departureTime.strftime('%H:%M')} → {conn.arrivalTime.strftime('%H:%M')} "
              f"({conn.durationText}, {len(conn.legs)-1} transfers)")
    
    # Example 4: Detailed view of the best connection
    if connections:
        best = connections[0]  # Usually the fastest/best option
        print(f"\n4. Detailed view of the best connection:")
        print(f"Trip: {originName} → {destName}")
        print(f"Total time: {best.durationText}")
        print(f"Total legs: {len(best.legs)}")
        print()
        
        for i, leg in enumerate(best.legs, 1):
            mode = leg.transportMode.name.title()
            print(f"Leg {i}: {mode}")
            print(f"  Line: {leg.line}")
            print(f"  From: {leg.origin.name}")
            print(f"  To: {leg.destination.name}")
            if leg.departureTime:
                print(f"  Depart: {leg.departureTime.strftime('%H:%M')}")
            if leg.arrivalTime:
                print(f"  Arrive: {leg.arrivalTime.strftime('%H:%M')}")
            # Calculate leg duration
            if leg.departureTime and leg.arrivalTime:
                legDuration = int((leg.arrivalTime - leg.departureTime).total_seconds() / 60)
                print(f"  Duration: {legDuration} min")
            print()
    
    print("="*50)
    print("Tip: Use departure_time parameter to plan trips for specific times!")

if __name__ == "__main__":
    main()