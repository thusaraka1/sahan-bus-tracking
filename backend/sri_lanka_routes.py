"""
Sri Lanka National & Urban Bus Route Catalog.
Contains official route numbers, corridors, and ordered intermediate stops with exact GPS coordinates.
Enables searching directly by bus route number (e.g., '04', '138', '177', '01', '02').
"""

SRI_LANKA_ROUTES = [
    {
        "route_number": "04",
        "aliases": ["4", "04", "04-1", "chilaw", "puttalam", "route 04", "route 4"],
        "name": "Route 04: Colombo Fort ⇄ Chilaw",
        "corridor": "A3 Colombo - Puttalam Coastal Highway",
        "origin": "Colombo Fort",
        "destination": "Chilaw",
        "color": "#10B981",
        "estimated_distance": "79.8 km",
        "estimated_duration": "2 hours 45 mins",
        "agency": "NTC & Wayamba Provincial Passenger Transport Authority",
        "stops": [
            {"name": "Colombo Fort Bus Stand", "latitude": 6.9344, "longitude": 79.8520, "type": "departure"},
            {"name": "Peliyagoda Junction", "latitude": 6.9614, "longitude": 79.8831, "type": "waypoint"},
            {"name": "Wattala", "latitude": 6.9902, "longitude": 79.8911, "type": "waypoint"},
            {"name": "Kandana", "latitude": 7.0478, "longitude": 79.8943, "type": "waypoint"},
            {"name": "Ja-Ela Bus Stand", "latitude": 7.0747, "longitude": 79.8917, "type": "waypoint"},
            {"name": "Seeduwa", "latitude": 7.1367, "longitude": 79.8833, "type": "waypoint"},
            {"name": "Negombo Central Bus Stand", "latitude": 7.2094, "longitude": 79.8386, "type": "waypoint"},
            {"name": "Kochchikade", "latitude": 7.2612, "longitude": 79.8601, "type": "waypoint"},
            {"name": "Wennappuwa", "latitude": 7.3385, "longitude": 79.8385, "type": "waypoint"},
            {"name": "Marawila", "latitude": 7.4124, "longitude": 79.8228, "type": "waypoint"},
            {"name": "Mahawewa", "latitude": 7.4724, "longitude": 79.8189, "type": "waypoint"},
            {"name": "Madampe", "latitude": 7.5028, "longitude": 79.8402, "type": "waypoint"},
            {"name": "Chilaw Bus Stand", "latitude": 7.5758, "longitude": 79.7953, "type": "arrival"},
        ]
    },
    {
        "route_number": "01",
        "aliases": ["1", "01", "1-1", "kandy", "route 01", "route 1"],
        "name": "Route 01: Colombo Fort ⇄ Kandy",
        "corridor": "A1 Colombo - Kandy Highway",
        "origin": "Colombo Fort",
        "destination": "Kandy",
        "color": "#3B82F6",
        "estimated_distance": "115 km",
        "estimated_duration": "3 hours 30 mins",
        "agency": "National Transport Commission - Sri Lanka",
        "stops": [
            {"name": "Colombo Fort (Bastian Mawatha)", "latitude": 6.9336, "longitude": 79.8556, "type": "departure"},
            {"name": "Peliyagoda", "latitude": 6.9614, "longitude": 79.8831, "type": "waypoint"},
            {"name": "Kiribathgoda", "latitude": 6.9804, "longitude": 79.9284, "type": "waypoint"},
            {"name": "Kadawatha", "latitude": 7.0016, "longitude": 79.9529, "type": "waypoint"},
            {"name": "Nittambuwa", "latitude": 7.1452, "longitude": 80.0960, "type": "waypoint"},
            {"name": "Warakapola", "latitude": 7.2251, "longitude": 80.1983, "type": "waypoint"},
            {"name": "Ambepussa", "latitude": 7.2450, "longitude": 80.2050, "type": "waypoint"},
            {"name": "Kegalle Central Stand", "latitude": 7.2533, "longitude": 80.3464, "type": "waypoint"},
            {"name": "Mawanella", "latitude": 7.2530, "longitude": 80.4480, "type": "waypoint"},
            {"name": "Kadugannawa", "latitude": 7.2550, "longitude": 80.5230, "type": "waypoint"},
            {"name": "Peradeniya", "latitude": 7.2605, "longitude": 80.5960, "type": "waypoint"},
            {"name": "Kandy Goods Shed Bus Stand", "latitude": 7.2895, "longitude": 80.6307, "type": "arrival"},
        ]
    },
    {
        "route_number": "02",
        "aliases": ["2", "02", "galle", "matara", "route 02", "route 2"],
        "name": "Route 02: Colombo Fort ⇄ Galle / Matara",
        "corridor": "A2 Galle Road Coastal Highway",
        "origin": "Colombo Fort",
        "destination": "Galle",
        "color": "#F59E0B",
        "estimated_distance": "119 km",
        "estimated_duration": "3 hours 15 mins",
        "agency": "National Transport Commission - Sri Lanka",
        "stops": [
            {"name": "Colombo Fort Bus Stand", "latitude": 6.9344, "longitude": 79.8520, "type": "departure"},
            {"name": "Kollupitiya", "latitude": 6.9150, "longitude": 79.8510, "type": "waypoint"},
            {"name": "Bambalapitiya", "latitude": 6.8920, "longitude": 79.8550, "type": "waypoint"},
            {"name": "Dehiwala", "latitude": 6.8510, "longitude": 79.8650, "type": "waypoint"},
            {"name": "Moratuwa", "latitude": 6.7730, "longitude": 79.8816, "type": "waypoint"},
            {"name": "Panadura", "latitude": 6.7130, "longitude": 79.9070, "type": "waypoint"},
            {"name": "Kalutara North & South", "latitude": 6.5854, "longitude": 79.9607, "type": "waypoint"},
            {"name": "Beruwala", "latitude": 6.4788, "longitude": 79.9828, "type": "waypoint"},
            {"name": "Aluthgama", "latitude": 6.4310, "longitude": 79.9995, "type": "waypoint"},
            {"name": "Ambalangoda", "latitude": 6.2359, "longitude": 80.0543, "type": "waypoint"},
            {"name": "Hikkaduwa", "latitude": 6.1395, "longitude": 80.1063, "type": "waypoint"},
            {"name": "Galle Central Bus Stand", "latitude": 6.0367, "longitude": 80.2170, "type": "arrival"},
        ]
    },
    {
        "route_number": "138",
        "aliases": ["138", "maharagama", "homagama", "high level", "route 138"],
        "name": "Route 138: Pettah ⇄ Maharagama / Homagama",
        "corridor": "High Level Road Corridor",
        "origin": "Pettah",
        "destination": "Homagama",
        "color": "#8B5CF6",
        "estimated_distance": "22.5 km",
        "estimated_duration": "1 hour 15 mins",
        "agency": "Western Province Road Passenger Transport Authority",
        "stops": [
            {"name": "Pettah Main Bus Stand", "latitude": 6.9360, "longitude": 79.8500, "type": "departure"},
            {"name": "Technical Junction", "latitude": 6.9300, "longitude": 79.8560, "type": "waypoint"},
            {"name": "Town Hall (Lipton Circus)", "latitude": 6.9150, "longitude": 79.8670, "type": "waypoint"},
            {"name": "Borella Junction", "latitude": 6.9147, "longitude": 79.8773, "type": "waypoint"},
            {"name": "Narahenpita", "latitude": 6.8950, "longitude": 79.8840, "type": "waypoint"},
            {"name": "Kirulapone", "latitude": 6.8815, "longitude": 79.8763, "type": "waypoint"},
            {"name": "Nugegoda Supermarket", "latitude": 6.8649, "longitude": 79.8997, "type": "waypoint"},
            {"name": "Delkanda Junction", "latitude": 6.8560, "longitude": 79.9090, "type": "waypoint"},
            {"name": "Maharagama Central Stand", "latitude": 6.8480, "longitude": 79.9267, "type": "waypoint"},
            {"name": "Pannipitiya", "latitude": 6.8450, "longitude": 79.9450, "type": "waypoint"},
            {"name": "Kottawa Junction", "latitude": 6.8410, "longitude": 79.9650, "type": "waypoint"},
            {"name": "Makumbura Multimodal Hub", "latitude": 6.8370, "longitude": 79.9880, "type": "waypoint"},
            {"name": "Homagama Bus Stand", "latitude": 6.8415, "longitude": 80.0030, "type": "arrival"},
        ]
    },
    {
        "route_number": "177",
        "aliases": ["177", "kaduwela", "malabe", "battaramulla", "route 177"],
        "name": "Route 177: Kollupitiya ⇄ Kaduwela",
        "corridor": "B240 Parliament & IT Corridor",
        "origin": "Kollupitiya",
        "destination": "Kaduwela",
        "color": "#06B6D4",
        "estimated_distance": "19.8 km",
        "estimated_duration": "1 hour 5 mins",
        "agency": "Western Province Road Passenger Transport Authority",
        "stops": [
            {"name": "Kollupitiya Junction", "latitude": 6.9150, "longitude": 79.8510, "type": "departure"},
            {"name": "Town Hall (Public Library)", "latitude": 6.9150, "longitude": 79.8670, "type": "waypoint"},
            {"name": "Borella Junction", "latitude": 6.9147, "longitude": 79.8773, "type": "waypoint"},
            {"name": "Rajagiriya", "latitude": 6.9080, "longitude": 79.8940, "type": "waypoint"},
            {"name": "Battaramulla", "latitude": 6.8990, "longitude": 79.9190, "type": "waypoint"},
            {"name": "Koswatte", "latitude": 6.9070, "longitude": 79.9280, "type": "waypoint"},
            {"name": "Thalahena", "latitude": 6.9130, "longitude": 79.9400, "type": "waypoint"},
            {"name": "Malabe Junction", "latitude": 6.9040, "longitude": 79.9550, "type": "waypoint"},
            {"name": "Kaduwela Central Stand", "latitude": 6.9340, "longitude": 79.9830, "type": "arrival"},
        ]
    },
    {
        "route_number": "120",
        "aliases": ["120", "horana", "piliyandala", "route 120"],
        "name": "Route 120: Pettah ⇄ Horana",
        "corridor": "Horana Road Corridor",
        "origin": "Pettah",
        "destination": "Horana",
        "color": "#EC4899",
        "estimated_distance": "32.0 km",
        "estimated_duration": "1 hour 35 mins",
        "agency": "Western Province Road Passenger Transport Authority",
        "stops": [
            {"name": "Pettah Main Stand", "latitude": 6.9360, "longitude": 79.8500, "type": "departure"},
            {"name": "Thimbirigasyaya", "latitude": 6.8910, "longitude": 79.8640, "type": "waypoint"},
            {"name": "Kohuwala", "latitude": 6.8610, "longitude": 79.8830, "type": "waypoint"},
            {"name": "Boralesgamuwa", "latitude": 6.8400, "longitude": 79.9020, "type": "waypoint"},
            {"name": "Piliyandala Clock Tower", "latitude": 6.8010, "longitude": 79.9220, "type": "waypoint"},
            {"name": "Kahathuduwa", "latitude": 6.7720, "longitude": 79.9650, "type": "waypoint"},
            {"name": "Pokunuwita", "latitude": 6.7450, "longitude": 80.0120, "type": "waypoint"},
            {"name": "Horana Bus Stand", "latitude": 6.7160, "longitude": 80.0630, "type": "arrival"},
        ]
    },
    {
        "route_number": "187",
        "aliases": ["187", "airport", "katunayake", "katunayake airport", "route 187"],
        "name": "Route 187: Colombo Fort ⇄ Katunayake Airport",
        "corridor": "Airport Expressway / Negombo Rd",
        "origin": "Colombo Fort",
        "destination": "Katunayake Airport",
        "color": "#3B82F6",
        "estimated_distance": "34.5 km",
        "estimated_duration": "45 mins (Expressway)",
        "agency": "National Transport Commission - Sri Lanka",
        "stops": [
            {"name": "Colombo Fort (Bastian Mawatha)", "latitude": 6.9336, "longitude": 79.8556, "type": "departure"},
            {"name": "Peliyagoda Interchange", "latitude": 6.9614, "longitude": 79.8831, "type": "waypoint"},
            {"name": "Ja-Ela Expressway Exit", "latitude": 7.0747, "longitude": 79.8917, "type": "waypoint"},
            {"name": "Katunayake Airport Terminal (BIA)", "latitude": 7.1808, "longitude": 79.8841, "type": "arrival"},
        ]
    },
    {
        "route_number": "240",
        "aliases": ["240", "negombo", "route 240"],
        "name": "Route 240: Colombo Fort ⇄ Negombo",
        "corridor": "A3 Colombo - Negombo Road",
        "origin": "Colombo Fort",
        "destination": "Negombo",
        "color": "#14B8A6",
        "estimated_distance": "37.2 km",
        "estimated_duration": "1 hour 25 mins",
        "agency": "Western Province Road Passenger Transport Authority",
        "stops": [
            {"name": "Colombo Fort Bus Stand", "latitude": 6.9344, "longitude": 79.8520, "type": "departure"},
            {"name": "Peliyagoda", "latitude": 6.9614, "longitude": 79.8831, "type": "waypoint"},
            {"name": "Wattala", "latitude": 6.9902, "longitude": 79.8911, "type": "waypoint"},
            {"name": "Kandana", "latitude": 7.0478, "longitude": 79.8943, "type": "waypoint"},
            {"name": "Ja-Ela", "latitude": 7.0747, "longitude": 79.8917, "type": "waypoint"},
            {"name": "Seeduwa", "latitude": 7.1367, "longitude": 79.8833, "type": "waypoint"},
            {"name": "Kurana", "latitude": 7.1820, "longitude": 79.8650, "type": "waypoint"},
            {"name": "Negombo Bus Stand", "latitude": 7.2094, "longitude": 79.8386, "type": "arrival"},
        ]
    },
    {
        "route_number": "87",
        "aliases": ["87", "jaffna", "vavuniya", "route 87", "87/769", "87-6-1"],
        "name": "Route 87: Colombo Fort ⇄ Jaffna / Vavuniya",
        "corridor": "A9 Northern Highway Corridor",
        "origin": "Colombo Fort",
        "destination": "Jaffna",
        "color": "#EF4444",
        "estimated_distance": "396 km",
        "estimated_duration": "8 hours 15 mins",
        "agency": "National Transport Commission - Sri Lanka",
        "stops": [
            {"name": "Colombo Fort (Bastian Mawatha)", "latitude": 6.9336, "longitude": 79.8556, "type": "departure"},
            {"name": "Negombo Central Stand", "latitude": 7.2094, "longitude": 79.8386, "type": "waypoint"},
            {"name": "Chilaw Bus Stand", "latitude": 7.5758, "longitude": 79.7953, "type": "waypoint"},
            {"name": "Puttalam Central Stand", "latitude": 8.0333, "longitude": 79.8333, "type": "waypoint"},
            {"name": "Medawachchiya Junction", "latitude": 8.5410, "longitude": 80.4930, "type": "waypoint"},
            {"name": "Vavuniya Central Bus Stand", "latitude": 8.7514, "longitude": 80.4971, "type": "waypoint"},
            {"name": "Kilinochchi Central Stand", "latitude": 9.3803, "longitude": 80.3992, "type": "waypoint"},
            {"name": "Jaffna Central Bus Station", "latitude": 9.6615, "longitude": 80.0255, "type": "arrival"},
        ]
    },
    {
        "route_number": "100",
        "aliases": ["100", "panadura", "galle road", "route 100"],
        "name": "Route 100: Pettah ⇄ Panadura",
        "corridor": "Galle Road Coastal Corridor",
        "origin": "Pettah",
        "destination": "Panadura",
        "color": "#6366F1",
        "estimated_distance": "27.5 km",
        "estimated_duration": "1 hour 20 mins",
        "agency": "Western Province Road Passenger Transport Authority",
        "stops": [
            {"name": "Pettah Bus Stand", "latitude": 6.9360, "longitude": 79.8500, "type": "departure"},
            {"name": "Galle Face Green", "latitude": 6.9240, "longitude": 79.8450, "type": "waypoint"},
            {"name": "Kollupitiya", "latitude": 6.9150, "longitude": 79.8510, "type": "waypoint"},
            {"name": "Bambalapitiya", "latitude": 6.8920, "longitude": 79.8550, "type": "waypoint"},
            {"name": "Wellawatte", "latitude": 6.8740, "longitude": 79.8600, "type": "waypoint"},
            {"name": "Dehiwala Junction", "latitude": 6.8510, "longitude": 79.8650, "type": "waypoint"},
            {"name": "Mt. Lavinia Hotel Junction", "latitude": 6.8350, "longitude": 79.8670, "type": "waypoint"},
            {"name": "Ratmalana", "latitude": 6.8180, "longitude": 79.8730, "type": "waypoint"},
            {"name": "Moratuwa Bus Stand", "latitude": 6.7730, "longitude": 79.8816, "type": "waypoint"},
            {"name": "Panadura Central Bus Stand", "latitude": 6.7130, "longitude": 79.9070, "type": "arrival"},
        ]
    },
    {
        "route_number": "05",
        "aliases": ["5", "05", "kurunegala", "route 05", "route 5"],
        "name": "Route 05: Colombo Fort ⇄ Kurunegala",
        "corridor": "Via Minuwangoda, Giriulla & Narammala",
        "origin": "Colombo Fort",
        "destination": "Kurunegala",
        "color": "#F97316",
        "estimated_distance": "93.4 km",
        "estimated_duration": "2 hours 50 mins",
        "agency": "National Transport Commission - Sri Lanka",
        "stops": [
            {"name": "Colombo Fort Bus Stand", "latitude": 6.9344, "longitude": 79.8520, "type": "departure"},
            {"name": "Ja-Ela", "latitude": 7.0747, "longitude": 79.8917, "type": "waypoint"},
            {"name": "Minuwangoda", "latitude": 7.1680, "longitude": 79.9530, "type": "waypoint"},
            {"name": "Divulapitiya", "latitude": 7.2280, "longitude": 80.0070, "type": "waypoint"},
            {"name": "Giriulla", "latitude": 7.3400, "longitude": 80.1200, "type": "waypoint"},
            {"name": "Narammala", "latitude": 7.4330, "longitude": 80.2150, "type": "waypoint"},
            {"name": "Kurunegala Central Stand", "latitude": 7.4860, "longitude": 80.3640, "type": "arrival"},
        ]
    },
    {
        "route_number": "99",
        "aliases": ["99", "badulla", "bandarawela", "route 99"],
        "name": "Route 99: Colombo ⇄ Badulla / Passara",
        "corridor": "A4 High Level & Sabaragamuwa Highway",
        "origin": "Colombo Fort",
        "destination": "Badulla",
        "color": "#A855F7",
        "estimated_distance": "226 km",
        "estimated_duration": "5 hours 45 mins",
        "agency": "National Transport Commission - Sri Lanka",
        "stops": [
            {"name": "Colombo Fort (Bastian Mawatha)", "latitude": 6.9336, "longitude": 79.8556, "type": "departure"},
            {"name": "Avissawella", "latitude": 6.9530, "longitude": 80.2070, "type": "waypoint"},
            {"name": "Ratnapura Clock Tower", "latitude": 6.6828, "longitude": 80.4037, "type": "waypoint"},
            {"name": "Pelmadulla", "latitude": 6.6234, "longitude": 80.5512, "type": "waypoint"},
            {"name": "Balangoda", "latitude": 6.6500, "longitude": 80.7000, "type": "waypoint"},
            {"name": "Beragala Junction", "latitude": 6.7780, "longitude": 80.9160, "type": "waypoint"},
            {"name": "Haputale", "latitude": 6.7680, "longitude": 80.9570, "type": "waypoint"},
            {"name": "Bandarawela Bus Stand", "latitude": 6.8300, "longitude": 80.9990, "type": "waypoint"},
            {"name": "Badulla Central Stand", "latitude": 6.9890, "longitude": 81.0560, "type": "arrival"},
        ]
    },
]


def lookup_route_by_number(query):
    """
    Search routes by route number (e.g. '04', '4', '138', '177') or town name.
    Returns matching catalog routes.
    """
    if not query:
        return SRI_LANKA_ROUTES[:6]

    clean_q = query.strip().lower()

    # Exact or alias match
    matches = []
    for r in SRI_LANKA_ROUTES:
        # Check direct number match
        if clean_q == r["route_number"].lower():
            matches.insert(0, r)
            continue
        # Check alias
        if any(clean_q == alias.lower() for alias in r["aliases"]):
            matches.insert(0, r)
            continue
        # Check partial alias / name
        if clean_q in r["name"].lower() or any(clean_q in alias.lower() for alias in r["aliases"]):
            matches.append(r)

    return matches
