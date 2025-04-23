import requests
from email.utils import formatdate
from xml.dom.minidom import parseString

# Deine Zugangsdaten
TRIAS_URL = "https://efastatic.vvs.de/unistuttgart/trias"
REQUESTOR_REF = "uni0719"

# Aktueller Zeitstempel im richtigen Format (falls du ihn brauchst)
timestamp = formatdate(usegmt=True)

# Deine XML-Anfrage (Zeitpunkt ist hier fix)
payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<Trias version="1.2" xmlns="http://www.vdv.de/trias" xmlns:siri="http://www.siri.org.uk/siri">
	<ServiceRequest>
		<siri:RequestTimestamp>2025-04-22T12:00:00</siri:RequestTimestamp>
		<siri:RequestorRef>{REQUESTOR_REF}</siri:RequestorRef>
		<RequestPayload>
		    <StopEventRequest>
                <Location>
					<LocationRef>
						<StopPointRef>de:08118:7402</StopPointRef>	
					</LocationRef>
					<DepArrTime>2025-04-22T18:00:00</DepArrTime>
				</Location>
				<Params>
					<NumberOfResults>40</NumberOfResults>
					<StopEventType>departure</StopEventType>
					<PtModeFilter>
						<Exclude>false</Exclude>
						<BusSubmode>localBus</BusSubmode>
					</PtModeFilter>
					<IncludeRealtimeData>true</IncludeRealtimeData>
				</Params>
            </StopEventRequest>
        </RequestPayload>
    </ServiceRequest>
</Trias>
"""

headers = {
    "Content-Type": "text/xml"
}

# Anfrage senden
response = requests.post(TRIAS_URL, data=payload.encode("utf-8"), headers=headers)

# Antwort verarbeiten und schön formatieren
if response.status_code == 200:
    pretty_xml = parseString(response.text).toprettyxml(indent="  ")
    print("✅ Erfolgreich! Formatierte XML-Antwort:\n")
    print(pretty_xml)
else:
    print("❌ Fehler beim Abruf der Daten")
    print("Status Code:", response.status_code)
    print("Antwort:")
    print(response.text)
