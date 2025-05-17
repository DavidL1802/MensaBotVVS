from src.utils import findStops, requestTrip, checkTrainDisruptions

stops = findStops("Urbach")
if(stops is not None):
    for triple in stops:
        # print(triple)
        pass

stops = findStops("Hauptbahnhof")
if(stops is not None):
    for triple in stops:
        print(triple)

stops = findStops("Universität")
if(stops is not None):
    for triple in stops:
        print(triple)

trips = requestTrip("de:08119:5789", "de:08111:6008")#, "2025-05-16T13:40:49")
for trip in trips:
    print(f'{trip["line"]} um {trip["departureTimeTable"]} (+{trip["departureDelay"]} min) von {trip["startLocation"]} ({trip["startPlatform"]}) -> {trip["endLocation"]} ({trip["endPlatform"]}) Ankunft um {trip["arrival"]} ({trip["duration"]})')

checkTrainDisruptions("de:08119:5789", "de:08111:6008")