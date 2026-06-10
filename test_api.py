import requests, json

url = 'http://127.0.0.1:5000/api/predict'
payload = {
    "property_type": "House",
    "location": "Kacyiru",
    "bedrooms": 2,
    "bathrooms": 1,
    "amenities_count": 3,
    "furnished_status": "Unfurnished",
    "road_access": "Good",
    "parking": "Yes",
    "security": "Yes"
}

headers = {'Content-Type': 'application/json'}
response = requests.post(url, headers=headers, data=json.dumps(payload))
print('Status code:', response.status_code)
print('Response JSON:', response.json())
