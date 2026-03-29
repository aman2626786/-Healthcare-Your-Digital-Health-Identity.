import sqlite3
import urllib.request
import urllib.parse
import json
import time
import os

db_path = os.path.join(r"e:\Swasthya-Sampark---Emergency-Response-Data-Management-System-main\backend", "health_system.db")
con = sqlite3.connect(db_path)
cur = con.cursor()

cur.execute("SELECT id, name, district, state FROM hospitals WHERE latitude IS NULL OR longitude IS NULL")
hospitals = cur.fetchall()

def geocode(location_name):
    query = urllib.parse.quote(location_name)
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'SwasthyaSampark/1.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Error geocoding {location_name}: {e}")
    return None, None

for hid, name, district, state in hospitals:
    address = []
    if district: address.append(district)
    if state: address.append(state)
    address.append("India")
    
    query_str = ", ".join(address)
    print(f"Geocoding ID {hid}: {name} at {query_str}")
    
    lat, lon = geocode(query_str)
    
    # Fallback to state level if district not found
    if not lat and state:
        lat, lon = geocode(f"{state}, India")
        
    if lat and lon:
        print(f"  Found: {lat}, {lon}")
        cur.execute("UPDATE hospitals SET latitude = ?, longitude = ?, abha_connected = 1 WHERE id = ?", (lat, lon, hid))
        con.commit()
    else:
        print("  Not found. Using dummy New Delhi coords.")
        cur.execute("UPDATE hospitals SET latitude = ?, longitude = ?, abha_connected = 1 WHERE id = ?", (28.6139, 77.2090, hid))
        con.commit()
        
    time.sleep(1) # Be nice to nominatim API rate limit (1 sec per request max)

print("Done geocoding.")
con.close()
