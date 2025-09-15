from skyscanner import SkyScanner
import datetime
import json

scanner = SkyScanner()

locations = scanner.search_locations("London")
pickup_location = locations[0]

# Search car rentals
rentals = scanner.get_car_rental(
    origin=pickup_location,
    depart_time=datetime.datetime(2025, 9, 20, 10, 0),
    return_time=datetime.datetime(2025, 9, 25, 10, 0),
    is_driver_over_25=True
)

with open('rentals.json','w') as f:
    json.dump(rentals,f)