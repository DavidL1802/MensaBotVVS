"""
Departure statistics collection for VVS transport data.

This module has been updated to work with the new PyVVS project structure:
- Uses camelCase naming convention throughout
- Imports from the new models.py and tools.py modules
- Uses the updated Departure dataclass with proper field names
- Integrates with the listDepartures function from tools.py
"""

import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set

from tools import listDepartures
from models import Departure

class DepartureStatistics:
    """
    A class to collect and manage departure statistics in a CSV file.
    
    Updated for the new PyVVS project with:
    - camelCase naming convention
    - Integration with new Departure model
    - Use of listDepartures from tools.py
    """
    
    def __init__(self, csvFilename: str = None):
        """
        Initialize the statistics collector.
        
        Args:
            csvFilename (str): Name of the CSV file to store statistics. 
                              If None, files will be created dynamically based on departure dates.
        """
        self.csvFilename = csvFilename
        self.headers = ["JourneyRef", "DateTime", "Line", "Delay"]
        self.existingJourneyRefs = set()
        
        # Load existing journey refs if file exists and filename is provided
        if csvFilename:
            self._loadExistingJourneyRefs()
    
    def _loadExistingJourneyRefs(self) -> None:
        """Load existing journey references from the CSV file."""
        if self.csvFilename and os.path.exists(self.csvFilename):
            try:
                with open(self.csvFilename, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        self.existingJourneyRefs.add(row['JourneyRef'])
            except Exception as e:
                print(f"❌ Error loading existing journey refs: {str(e)}")
    
    def _createCsvIfNotExists(self) -> None:
        """Create the CSV file with headers if it doesn't exist."""
        if self.csvFilename and not os.path.exists(self.csvFilename):
            try:
                with open(self.csvFilename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(self.headers)
                print(f"✅ Created new CSV file: {self.csvFilename}")
            except Exception as e:
                print(f"❌ Error creating CSV file: {str(e)}")
    
    def _updateExistingJourney(self, journeyRef: str, delay: int) -> bool:
        """
        Update the delay for an existing journey if delay data is available.
        
        Args:
            journeyRef (str): The journey reference to update.
            delay (int): The new delay value.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not os.path.exists(self.csvFilename):
            return False
        
        try:
            # Read all rows
            rows = []
            with open(self.csvFilename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['JourneyRef'] == journeyRef and delay is not None:
                        # Update delay if we have delay data
                        row['Delay'] = str(delay)
                        print(f"🔄 Updated delay for {journeyRef}: {delay} min")
                    rows.append(row)
            
            # Write back all rows
            with open(self.csvFilename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(rows)
            
            return True
        except Exception as e:
            print(f"❌ Error updating journey: {str(e)}")
            return False
    
    def _addNewJourney(self, journeyRef: str, line: str, delay: int, departureDateTime: datetime) -> bool:
        """
        Add a new journey to the CSV file.
        
        Args:
            journeyRef (str): The journey reference.
            line (str): The line number/name.
            delay (int): The delay in minutes.
            departureDateTime (datetime): The actual scheduled departure datetime.
            
        Returns:
            bool: True if addition was successful, False otherwise.
        """
        try:
            with open(self.csvFilename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Use the actual departure datetime from the API
                departureStr = departureDateTime.strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([journeyRef, departureStr, line, delay if delay is not None else ""])
                
            self.existingJourneyRefs.add(journeyRef)
            displayTime = departureDateTime.strftime("%H:%M")
            delayText = f"{delay} min" if delay is not None else "unknown delay"
            print(f"➕ Added new journey: {journeyRef} (Line {line}, Departure: {displayTime}, Delay: {delayText})")
            return True
        except Exception as e:
            print(f"❌ Error adding new journey: {str(e)}")
            return False
            return True
        except Exception as e:
            print(f"❌ Error adding new journey: {str(e)}")
            return False
    
    def collectStatistics(self, stopPointRef: str) -> None:
        """
        Collect departure statistics for a given stop, organizing by departure date.
        
        Args:
            stopPointRef (str): The stop point reference to collect data for.
        """
        print(f"📊 Collecting departure statistics for stop: {stopPointRef}")
        
        # Calculate departure time as 30 minutes ago
        thirtyMinutesAgo = datetime.now() - timedelta(minutes=30)
        
        # Get departures from 30 minutes ago with limited results
        departures = listDepartures(
            stopId=stopPointRef, 
            departureTime=thirtyMinutesAgo,
            numberOfResults=25
        )
        
        print(f"🕐 Retrieving departures from: {thirtyMinutesAgo.strftime('%H:%M:%S')} (30 minutes ago)")
        print(f"📝 Limiting results to: 15 departures")
        
        if not departures:
            print("❌ No departures found or error occurred.")
            return
        
        # Group departures by date
        departuresByDate = {}
        
        for departure in departures:
            journeyRef = departure.journeyRef
            line = departure.line
            delay = departure.delayMinutes
            scheduledDateTime = departure.scheduledDateTime
            
            # Skip if we don't have essential data
            if not journeyRef or not line or not scheduledDateTime:
                continue
            
            # Extract date from scheduled datetime
            print(scheduledDateTime)
            departureDate = scheduledDateTime.strftime("%d_%m_%Y")
            
            if departureDate not in departuresByDate:
                departuresByDate[departureDate] = []
            
            departuresByDate[departureDate].append({
                'departure': departure,
                'journeyRef': journeyRef,
                'line': line,
                'delay': delay,
                'scheduledDateTime': scheduledDateTime
            })
        
        # Process each date separately
        totalNewEntries = 0
        totalUpdatedEntries = 0
        
        for departureDate, dateDepartures in departuresByDate.items():
            print(f"\n📅 Processing departures for date: {departureDate}")
            
            # Create statistics collector for this specific date
            csvFilename = f"statistics/{departureDate}.csv"
            dateStatsCollector = DepartureStatistics(csvFilename)
            
            # Ensure CSV file exists with headers
            dateStatsCollector._createCsvIfNotExists()
            
            newEntries = 0
            updatedEntries = 0
            
            for depData in dateDepartures:
                journeyRef = depData['journeyRef']
                line = depData['line']
                delay = depData['delay']
                scheduledDateTime = depData['scheduledDateTime']
                
                # Check if journey already exists
                if journeyRef in dateStatsCollector.existingJourneyRefs:
                    # Update existing journey if we have delay data
                    if delay is not None:
                        if dateStatsCollector._updateExistingJourney(journeyRef, delay):
                            updatedEntries += 1
                else:
                    # Add new journey
                    if dateStatsCollector._addNewJourney(journeyRef, line, delay, scheduledDateTime):
                        newEntries += 1
            
            print(f"   📈 New entries added: {newEntries}")
            print(f"   🔄 Entries updated: {updatedEntries}")
            print(f"   📁 Data saved to: {csvFilename}")
            
            totalNewEntries += newEntries
            totalUpdatedEntries += updatedEntries
        
        print(f"\n✅ Statistics collection complete:")
        print(f"   📈 Total new entries added: {totalNewEntries}")
        print(f"   🔄 Total entries updated: {totalUpdatedEntries}")
        print(f"   � Files organized by departure date")
    
    def printSummary(self) -> None:
        """Print a summary of the collected statistics."""
        if not os.path.exists(self.csvFilename):
            print("❌ No statistics file found.")
            return
        
        try:
            with open(self.csvFilename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                
                if not rows:
                    print("📊 No statistics data available.")
                    return
                
                print(f"\n📊 Statistics Summary from {self.csvFilename}:")
                print("-" * 60)
                print(f"Total journeys tracked: {len(rows)}")
                
                # Count by line
                lineCounts = {}
                delaysWithData = []
                
                for row in rows:
                    line = row['Line']
                    delayStr = row['Delay']
                    
                    lineCounts[line] = lineCounts.get(line, 0) + 1
                    
                    if delayStr and delayStr.strip():
                        try:
                            delay = int(delayStr)
                            delaysWithData.append(delay)
                        except ValueError:
                            pass
                
                print(f"Lines tracked: {', '.join(sorted(lineCounts.keys()))}")
                
                for line, count in sorted(lineCounts.items()):
                    print(f"  - Line {line}: {count} journeys")
                
                if delaysWithData:
                    avgDelay = sum(delaysWithData) / len(delaysWithData)
                    maxDelay = max(delaysWithData)
                    minDelay = min(delaysWithData)
                    
                    print(f"\nDelay Statistics:")
                    print(f"  - Journeys with delay data: {len(delaysWithData)}")
                    print(f"  - Average delay: {avgDelay:.1f} minutes")
                    print(f"  - Maximum delay: {maxDelay} minutes")
                    print(f"  - Minimum delay: {minDelay} minutes")
                
        except Exception as e:
            print(f"❌ Error reading statistics: {str(e)}")


def main():
    """Main function to run the statistics collection."""
    stopId = "de:08111:6008"
    
    # Create statistics directory if it doesn't exist
    if not os.path.exists("statistics"):
        os.makedirs("statistics")
    
    # Create a temporary collector just for the collection process
    # The actual files will be created based on departure dates
    statsCollector = DepartureStatistics()
    
    print("🚌 VVS Departure Statistics Collector")
    print("=" * 50)
    
    # Collect current statistics (this will create files based on departure dates)
    statsCollector.collectStatistics(stopId)
    
    # Print summaries for all CSV files in statistics directory
    print("\n📈 Summary of all statistics files:")
    print("=" * 50)
    
    for filename in sorted(os.listdir("statistics")):
        if filename.endswith(".csv"):
            filepath = f"statistics/{filename}"
            print(f"\n📊 Summary for {filename}:")
            print("-" * 40)
            tempCollector = DepartureStatistics(filepath)
            tempCollector.printSummary()


if __name__ == "__main__":
    main()