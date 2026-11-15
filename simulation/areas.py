"""Coarse Cairo areas used as trip origins and destinations.

The M1 proposal lists "~50 Cairo areas" from OpenStreetMap. The coordinates
below were typed in by hand as approximate area centres (about 1 km accuracy).
They are good enough for simulating distances, but they were NOT downloaded
from OpenStreetMap. They were compared with OpenStreetMap on 15 Nov 2026 using
``python -m simulation.check_areas_osm`` (see data/README.md for the result);
OpenStreetMap contributors, ODbL, https://www.openstreetmap.org.

Each entry: (name, zone, latitude, longitude, popularity)

``popularity`` is a relative weight used when choosing trip destinations
(universities, business districts and the new cities attract more trips).
"""

AREAS = [
    # Central Cairo
    ("Downtown", "Central Cairo", 30.0444, 31.2357, 5),
    ("Garden City", "Central Cairo", 30.0360, 31.2310, 2),
    ("Zamalek", "Central Cairo", 30.0609, 31.2194, 3),
    ("Boulaq", "Central Cairo", 30.0570, 31.2300, 1),
    ("Ramses", "Central Cairo", 30.0620, 31.2480, 3),
    ("Sayeda Zeinab", "Central Cairo", 30.0300, 31.2400, 2),
    ("Old Cairo", "Central Cairo", 30.0050, 31.2300, 2),
    ("Manial", "Central Cairo", 30.0200, 31.2250, 1),
    ("Shubra", "Central Cairo", 30.0714, 31.2450, 2),
    ("Rod El Farag", "Central Cairo", 30.1000, 31.2400, 1),
    ("Shubra El Kheima", "Central Cairo", 30.1286, 31.2422, 2),
    # Giza
    ("Giza Square", "Giza", 30.0131, 31.2089, 3),
    ("Dokki", "Giza", 30.0384, 31.2118, 3),
    ("Mohandessin", "Giza", 30.0500, 31.2000, 4),
    ("Agouza", "Giza", 30.0580, 31.2100, 2),
    ("Imbaba", "Giza", 30.0700, 31.2100, 1),
    ("Haram", "Giza", 29.9870, 31.1700, 2),
    ("Faisal", "Giza", 30.0100, 31.1800, 2),
    ("Cairo University", "Giza", 30.0262, 31.2085, 4),
    # South
    ("Maadi", "South Cairo", 29.9602, 31.2569, 4),
    ("Basatin", "South Cairo", 29.9830, 31.2830, 1),
    ("Dar El Salam", "South Cairo", 29.9800, 31.2450, 1),
    ("Torah", "South Cairo", 29.9400, 31.2900, 1),
    ("Helwan", "South Cairo", 29.8414, 31.3342, 2),
    ("15th of May City", "South Cairo", 29.8600, 31.3600, 1),
    ("Mokattam", "South Cairo", 30.0130, 31.3000, 2),
    # East
    ("Heliopolis", "East Cairo", 30.0911, 31.3225, 4),
    ("Nasr City", "East Cairo", 30.0561, 31.3301, 5),
    ("Abbassia", "East Cairo", 30.0720, 31.2830, 2),
    ("Hadayek El Kobba", "East Cairo", 30.0900, 31.2800, 1),
    ("Zeitoun", "East Cairo", 30.1050, 31.3050, 1),
    ("Matareya", "East Cairo", 30.1200, 31.3150, 1),
    ("Ain Shams", "East Cairo", 30.1310, 31.3190, 2),
    ("El Nozha", "East Cairo", 30.1088, 31.3419, 2),
    ("Sheraton", "East Cairo", 30.1050, 31.3800, 2),
    ("Merghany", "East Cairo", 30.0900, 31.3330, 1),
    ("Cairo Airport", "East Cairo", 30.1219, 31.4056, 3),
    ("Obour City", "East Cairo", 30.2283, 31.4772, 2),
    # New Cairo and eastern new cities
    ("New Cairo (5th Settlement)", "New Cairo", 30.0074, 31.4913, 5),
    ("AUC New Cairo", "New Cairo", 30.0194, 31.4998, 4),
    ("Cairo Festival City", "New Cairo", 30.0290, 31.4090, 3),
    ("El Rehab", "New Cairo", 30.0596, 31.4916, 3),
    ("Katameya", "New Cairo", 29.9900, 31.4200, 2),
    ("Madinaty", "New Cairo", 30.1000, 31.6400, 3),
    ("El Shorouk", "New Cairo", 30.1167, 31.6000, 2),
    ("New Administrative Capital", "New Cairo", 30.0200, 31.7600, 4),
    # West: 6th of October and Sheikh Zayed
    ("Sheikh Zayed", "West Cairo", 30.0131, 30.9880, 4),
    ("6th of October City", "West Cairo", 29.9285, 30.9188, 4),
    ("Dreamland", "West Cairo", 29.9550, 30.9400, 2),
    ("Badya University area", "West Cairo", 29.9890, 30.9420, 4),
]
