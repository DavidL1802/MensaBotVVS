from src.utils import findStops, requestTrip

stops = findStops("Universität")
for triple in stops:
    print(triple)

requestTrip("de:08111:6555", "de:08111:6556")
