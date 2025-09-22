import csv
import os
from datetime import datetime
from departure import Departure
from typing import List, Dict, Set

class DepartureStatistics:
    """
    A class to collect and manage departure statistics in a CSV file.
    """
    
    def __init__(self, csv_filename: str = "departure_statistics.csv"):
        """
        Initialize the statistics collector.
        
        Args:
            csv_filename (str): Name of the CSV file to store statistics.
        """
        self.csv_filename = csv_filename
        self.headers = ["JourneyRef", "DateTime", "Line", "Delay"]
        self.existing_journey_refs = set()
        
        # Load existing journey refs if file exists
        self._load_existing_journey_refs()
    
    def _load_existing_journey_refs(self) -> None:
        """Load existing journey references from the CSV file."""
        if os.path.exists(self.csv_filename):
            try:
                with open(self.csv_filename, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        self.existing_journey_refs.add(row['JourneyRef'])
            except Exception as e:
                print(f"❌ Error loading existing journey refs: {str(e)}")
    
    def _create_csv_if_not_exists(self) -> None:
        """Create the CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_filename):
            try:
                with open(self.csv_filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(self.headers)
                print(f"✅ Created new CSV file: {self.csv_filename}")
            except Exception as e:
                print(f"❌ Error creating CSV file: {str(e)}")
    
    def _update_existing_journey(self, journey_ref: str, delay: int) -> bool:
        """
        Update the delay for an existing journey if delay data is available.
        
        Args:
            journey_ref (str): The journey reference to update.
            delay (int): The new delay value.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        if not os.path.exists(self.csv_filename):
            return False
        
        try:
            # Read all rows
            rows = []
            with open(self.csv_filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['JourneyRef'] == journey_ref and delay is not None:
                        # Update delay if we have delay data
                        row['Delay'] = str(delay)
                        print(f"🔄 Updated delay for {journey_ref}: {delay} min")
                    rows.append(row)
            
            # Write back all rows
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(rows)
            
            return True
        except Exception as e:
            print(f"❌ Error updating journey: {str(e)}")
            return False
    
    def _add_new_journey(self, journey_ref: str, line: str, delay: int, scheduled_time: str) -> bool:
        """
        Add a new journey to the CSV file.
        
        Args:
            journey_ref (str): The journey reference.
            line (str): The line number/name.
            delay (int): The delay in minutes.
            scheduled_time (str): The scheduled departure time.
            
        Returns:
            bool: True if addition was successful, False otherwise.
        """
        try:
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Use today's date with the scheduled time for the DateTime
                today = datetime.now().strftime("%Y-%m-%d")
                departure_datetime = f"{today} {scheduled_time}:00"
                writer.writerow([journey_ref, departure_datetime, line, delay if delay is not None else ""])
                
            self.existing_journey_refs.add(journey_ref)
            print(f"➕ Added new journey: {journey_ref} (Line {line}, Departure: {scheduled_time}, Delay: {delay} min)")
            return True
        except Exception as e:
            print(f"❌ Error adding new journey: {str(e)}")
            return False
    
    def collect_statistics(self, stop_point_ref: str) -> None:
        """
        Collect departure statistics for a given stop.
        
        Args:
            stop_point_ref (str): The stop point reference to collect data for.
        """
        print(f"📊 Collecting departure statistics for stop: {stop_point_ref}")
        
        # Create CSV file if it doesn't exist
        self._create_csv_if_not_exists()
        
        # Get departures
        departure_collector = Departure(stop_point_ref)
        departures = departure_collector.get_departures()
        
        if not departures:
            print("❌ No departures found or error occurred.")
            return
        
        new_entries = 0
        updated_entries = 0
        
        for departure in departures:
            journey_ref = departure.get("journey_ref")
            line = departure.get("line")
            delay = departure.get("delay")
            scheduled_time = departure.get("scheduled_time")
            
            # Skip if we don't have essential data
            if not journey_ref or not line or not scheduled_time:
                continue
            
            # Check if journey already exists
            if journey_ref in self.existing_journey_refs:
                # Update existing journey if we have delay data
                if delay is not None:
                    if self._update_existing_journey(journey_ref, delay):
                        updated_entries += 1
            else:
                # Add new journey
                if self._add_new_journey(journey_ref, line, delay, scheduled_time):
                    new_entries += 1
        
        print(f"✅ Statistics collection complete:")
        print(f"   📈 New entries added: {new_entries}")
        print(f"   🔄 Entries updated: {updated_entries}")
        print(f"   📁 Data saved to: {self.csv_filename}")
    
    def print_summary(self) -> None:
        """Print a summary of the collected statistics."""
        if not os.path.exists(self.csv_filename):
            print("❌ No statistics file found.")
            return
        
        try:
            with open(self.csv_filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                
                if not rows:
                    print("📊 No statistics data available.")
                    return
                
                print(f"\n📊 Statistics Summary from {self.csv_filename}:")
                print("-" * 60)
                print(f"Total journeys tracked: {len(rows)}")
                
                # Count by line
                line_counts = {}
                delays_with_data = []
                
                for row in rows:
                    line = row['Line']
                    delay_str = row['Delay']
                    
                    line_counts[line] = line_counts.get(line, 0) + 1
                    
                    if delay_str and delay_str.strip():
                        try:
                            delay = int(delay_str)
                            delays_with_data.append(delay)
                        except ValueError:
                            pass
                
                print(f"Lines tracked: {', '.join(sorted(line_counts.keys()))}")
                
                for line, count in sorted(line_counts.items()):
                    print(f"  - Line {line}: {count} journeys")
                
                if delays_with_data:
                    avg_delay = sum(delays_with_data) / len(delays_with_data)
                    max_delay = max(delays_with_data)
                    min_delay = min(delays_with_data)
                    
                    print(f"\nDelay Statistics:")
                    print(f"  - Journeys with delay data: {len(delays_with_data)}")
                    print(f"  - Average delay: {avg_delay:.1f} minutes")
                    print(f"  - Maximum delay: {max_delay} minutes")
                    print(f"  - Minimum delay: {min_delay} minutes")
                
        except Exception as e:
            print(f"❌ Error reading statistics: {str(e)}")


def main():
    """Main function to run the statistics collection."""
    stop_id = "de:08111:6008"
    stats_collector = DepartureStatistics()
    
    print("🚌 VVS Departure Statistics Collector")
    print("=" * 50)
    
    # Collect current statistics
    stats_collector.collect_statistics(stop_id)
    
    # Print summary
    stats_collector.print_summary()


if __name__ == "__main__":
    main()