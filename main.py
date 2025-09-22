from utils import find_stops, request_trip, check_train_disruptions
from departure import Departure

# stops = find_stops("Urbach")
# if(stops is not None):
#     for triple in stops:
#         # print(triple)
#         pass

# stops = find_stops("Hauptbahnhof")
# if(stops is not None):
#     for triple in stops:
#         print(triple)

# stops = find_stops("Universität")
# if(stops is not None):
#     for triple in stops:
#         print(triple)

# trips = request_trip("de:08119:5789", "de:08111:6008")#, "2025-05-16T13:40:49")
# if trips:
#     for trip in trips:
#         print(f'{trip["line"]} um {trip["departureTimeTable"]} (+{trip["departureDelay"]} min) von {trip["startLocation"]} ({trip["startPlatform"]}) -> {trip["endLocation"]} ({trip["endPlatform"]}) Ankunft um {trip["arrival"]} ({trip["duration"]})')

# check_train_disruptions("de:08119:5789", "de:08111:6008")

# Test departure functionality
print("\n" + "="*80)
print("Testing Departure API for stop 'de:08111:6008'")
print("="*80)

departure_test = Departure("de:08111:6008", departure_time="2025-09-22T18:00:00", number_of_results=5)
departure_test.print_departures()
departure_test.save_response_debug("departure_response.xml")