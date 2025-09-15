from skyscanner.types import CabinClass
from skyscanner import SkyScanner
import datetime
import json

scanner = SkyScanner()

JFK = scanner.get_airport_by_code('JFK')
MXP = scanner.get_airport_by_code('MXP')

prices = scanner.get_flight_prices(
    origin=JFK,
    destination=MXP,
    depart_date=datetime.datetime(2025, 9, 20, 10, 0),
    return_date=datetime.datetime(2025, 9, 25, 10, 0),
    adults=5,
    childAges=[9,13],
    cabinClass=CabinClass.FIRST
)
with open('prices.json','w') as f:
    json.dump(prices.json,f,indent=4)
    
buckets = prices.json['itineraries']['buckets']

best_bucket = next((bucket for bucket in buckets if bucket['id'].lower() == 'best'), None)

best_itinerary_id = best_bucket['items'][0]['id']

itinerary_details = scanner.get_itinerary_details(best_itinerary_id, prices)
with open('details.json','w') as f:
    json.dump(itinerary_details,f,indent=4)