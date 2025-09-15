# SkyScanner API Client Documentation

A Python client library for interacting with the Skyscanner flight and car rental APIs. This library provides a comprehensive interface for searching flights, airports, locations, and car rentals with built-in retry logic and error handling.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Class Reference](#class-reference)
- [Methods](#methods)
- [Types and Enums](#types-and-enums)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Installation

```bash
pip install curl_cffi typeguard
```

## Quick Start

```python
import datetime
from skyscanner import SkyScanner
from skyscanner.types import CabinClass, SpecialTypes

# Initialize the client
scanner = SkyScanner(
    locale="en-US",
    currency="USD",
    market="US"
)

# Search for airports
airports = scanner.search_airports("London")
origin = airports[0]  # First result

destination_airports = scanner.search_airports("New York")
destination = destination_airports[0]

# Search for flights
depart_date = datetime.datetime(2025, 8, 15)
return_date = datetime.datetime(2025, 8, 22)

response = scanner.get_flight_prices(
    origin=origin,
    destination=destination,
    depart_date=depart_date,
    return_date=return_date,
    cabinClass=CabinClass.ECONOMY,
    adults=2
)

```

## Class Reference

### SkyScanner

The main client class for interacting with Skyscanner APIs.

#### Constructor

```python
SkyScanner(
    locale: str = "en-US",
    currency: str = "USD", 
    market: str = "US",
    retry_delay: int = 2,
    max_retries: int = 15,
    proxies: dict = {},
    px_authorization: str | None = None,
    verify: bool = True
)
```

**Parameters:**
- `locale` (str): Locale code for results (e.g., "en-US", "fr-FR")
- `currency` (str): Currency code for pricing (e.g., "USD", "EUR", "GBP")
- `market` (str): Market region code (e.g., "US", "UK", "DE")
- `retry_delay` (int): Seconds to wait between polling retries
- `max_retries` (int): Maximum number of polling retries before giving up
- `proxies` (dict): Proxy configuration for HTTP requests
- `px_authorization` (str | None): Optional pre-generated PX authorization token
- `verify` (bool): Whether to verify SSL certificates

## Methods

### get_flight_prices()

Search for flight prices between two locations.

```python
get_flight_prices(
    origin: Airport,
    destination: Airport | SpecialTypes,
    depart_date: datetime.datetime | SpecialTypes | None = None,
    return_date: datetime.datetime | SpecialTypes | None = None,
    cabinClass: CabinClass = CabinClass.ECONOMY,
    adults: int = 1,
    childAges: list[int] = []
) -> SkyscannerResponse
```

**Parameters:**
- `origin` (Airport): Origin airport object
- `destination` (Airport | SpecialTypes): Destination airport or special search type (e.g., SpecialTypes.EVERYWHERE)
- `depart_date` (datetime | SpecialTypes | None): Departure date or SpecialTypes.ANYTIME
- `return_date` (datetime | SpecialTypes | None): Return date (optional for one-way trips)
- `cabinClass` (CabinClass): Cabin class preference
- `adults` (int): Number of adult passengers (1-8)
- `childAges` (list[int]): Ages of child passengers (0-17 years, max 8 children)

**Returns:** `SkyscannerResponse` object containing flight options and pricing data

**Raises:**
- `ValueError`: Invalid dates, passenger counts, or search parameters
- `BannedWithCaptcha`: When blocked by Skyscanner's anti-bot measures
- `AttemptsExhaustedIncompleteResponse`: When max retries exceeded

### search_airports()

Auto-suggest airports based on a search query.

```python
search_airports(
    query: str,
    depart_date: datetime.datetime | None = None,
    return_date: datetime.datetime | None = None
) -> list[Airport]
```

**Parameters:**
- `query` (str): Search text (airport name, city, or IATA code)
- `depart_date` (datetime | None): Optional departure date for context
- `return_date` (datetime | None): Optional return date for context

**Returns:** List of `Airport` objects matching the query

### search_locations()

Auto-suggest locations for car rentals and other services.

```python
search_locations(query: str) -> list[Location]
```

**Parameters:**
- `query` (str): Location search text

**Returns:** List of `Location` objects

### get_airport_by_code()

Retrieve a specific airport by its IATA code.

```python
get_airport_by_code(airport_code: str) -> Airport
```

**Parameters:**
- `airport_code` (str): Three-letter IATA airport code (e.g., "JFK", "LHR")

**Returns:** `Airport` object for the specified code

**Raises:**
- `GenericError`: If airport code not found

### get_itinerary_details()

Get detailed information for a specific flight itinerary.

```python
get_itinerary_details(
    itineraryId: str,
    response: SkyscannerResponse
) -> dict
```

**Parameters:**
- `itineraryId` (str): Unique itinerary identifier from search results
- `response` (SkyscannerResponse): Original search response containing session data

**Returns:** Dictionary with detailed itinerary information including flight legs and preferences

### get_car_rental()

Search for car rental options between locations and times.

```python
get_car_rental(
    origin: Location | Coordinates | Airport,
    depart_time: datetime.datetime,
    return_time: datetime.datetime,
    destination: Location | Coordinates | Airport | None = None,
    is_driver_over_25: bool = True
) -> dict
```

**Parameters:**
- `origin` (Location | Coordinates | Airport): Pickup location
- `depart_time` (datetime): Pickup date and time
- `return_time` (datetime): Drop-off date and time  
- `destination` (Location | Coordinates | Airport | None): Drop-off location (defaults to origin)
- `is_driver_over_25` (bool): Driver age flag affecting pricing

**Returns:** Dictionary containing car rental options and pricing

### get_car_rental_from_url()

Parse a Skyscanner car rental URL and fetch rental options.

```python
get_car_rental_from_url(url: str) -> dict
```

**Parameters:**
- `url` (str): Skyscanner car hire URL

**Returns:** Car rental search results

**Example URL format:**
```
https://www.skyscanner.net/g/carhire-quotes/GB/en-GB/GBP/30/27544008/27544008/2025-07-01T10:00/2025-08-01T10:00/
```

## Types and Enums

### Airport
```python
Airport(
    title: str,        # Display name (e.g., "London Heathrow")
    entityId: str,     # Internal Skyscanner ID
    skyId: str         # IATA code (e.g., "LHR")
)
```

### Location
```python
Location(
    name: str,         # Location name
    entity_id: str,    # Internal ID
    coordinates: str   # Lat/long coordinates
)
```

### CabinClass
- `CabinClass.ECONOMY`
- `CabinClass.PREMIUM_ECONOMY`  
- `CabinClass.BUSINESS`
- `CabinClass.FIRST`

### SpecialTypes
- `SpecialTypes.ANYTIME` - Flexible date search
- `SpecialTypes.EVERYWHERE` - Open destination search

## Error Handling

The library defines several custom exceptions:

### BannedWithCaptcha
Raised when Skyscanner blocks requests with CAPTCHA challenges.

```python
try:
    response = scanner.get_flight_prices(origin, destination)
except BannedWithCaptcha as e:
    print(f"Blocked by anti-bot measures: {e}")
    # Consider using proxies or reducing request frequency
```

### AttemptsExhaustedIncompleteResponse
Raised when polling retries are exhausted without getting complete results.

```python
try:
    response = scanner.get_flight_prices(origin, destination)
except AttemptsExhaustedIncompleteResponse:
    print("Search timed out - try again later")
```

### GenericError
General API errors with status codes and response details.

## Examples

### Basic Flight Search

```python
import datetime
from skyscanner import SkyScanner

scanner = SkyScanner()

# Find airports
london_airports = scanner.search_airports("London")
heathrow = london_airports[0]

nyc_airports = scanner.search_airports("New York")
jfk = nyc_airports[0]

# Search flights
response = scanner.get_flight_prices(
    origin=heathrow,
    destination=jfk,
    depart_date=datetime.datetime(2025, 9, 1),
    return_date=datetime.datetime(2025, 9, 8),
    adults=1
)

```

### Flexible Search (Anywhere, Anytime)

```python
from skyscanner.types import SpecialTypes

# Search from London to anywhere
response = scanner.get_flight_prices(
    origin=heathrow,
    destination=SpecialTypes.EVERYWHERE,
    depart_date=SpecialTypes.ANYTIME
)
```

### Car Rental Search

```python
# Search locations
locations = scanner.search_locations("London")
pickup_location = locations[0]

# Search car rentals
rentals = scanner.get_car_rental(
    origin=pickup_location,
    depart_time=datetime.datetime(2025, 7, 1, 10, 0),
    return_time=datetime.datetime(2025, 7, 8, 10, 0),
    is_driver_over_25=True
)

```

## Rate Limiting and Best Practices

1. **Use Proxies**: Consider proxy rotation for high-volume usage  
2. **Cache Results**: Store airport/location searches to reduce API calls
3. **Validate Inputs**: Check dates and passenger counts before API calls
4. **Reuse Px Authorization**: X-Px-Authorization header isn't signel use. Once you've made one you can use it for multiple requests, once you get captcha though you need to switch ip and authorization

## Dependencies

- `curl_cffi`: HTTP client with browser fingerprinting
- `typeguard`: Runtime type checking
- `orjson`: Fast JSON parsing


## TODO

- [ ] Add scraping flight prices from generic cities and not specific airports (like Milan and not MXP)
- [ ] Add async version
- [ ] Type better the flight price response to not always parse json
- [ ] Add method to build skyscanner buy link statically without requesting details