import urllib.request

url = "https://www.plantuml.com/plantuml/png/SoWkIImgAStDuNBAJrBGjLDmpCbCJbMmKiX8pSd9vt98pKi1IW80"
try:
    req = urllib.request.urlopen(url, timeout=10)
    print(f"PlantUML server OK, status={req.status}, size={len(req.read())} bytes")
except Exception as e:
    print(f"PlantUML server failed: {e}")
