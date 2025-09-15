import curl_cffi
import datetime
import time
import uuid
import orjson
from typeguard import typechecked
from . import config
from .px import PXSolver
from .types import Location, Airport, CabinClass, SpecialTypes, SkyscannerResponse, Coordinates
from .errors import AttemptsExhaustedIncompleteResponse, BannedWithCaptcha, GenericError

#TODO aggiungere scraping da qualsiasi (tipo Milano)
class SkyScanner:
    """
    A client for interacting with the Skyscanner flight and car rental APIs.

    This class handles search session creation, flight price lookups, airport and location
    autosuggestions, itinerary detail retrieval, and car rental listings, with built-in retry
    and error handling.
    """

    @typechecked
    def __init__(
        self,
        locale: str = "en-US",
        currency: str = "USD",
        market: str = "US",
        retry_delay: int = 2,
        max_retries: int = 15,
        proxy: str = '',
        px_authorization: str | None = None,
        verify : bool = True
    ):
        """
        Initialize the SkyScanner client.

        Args:
            locale (str): Locale code for results (default: "en-US").
            currency (str): Currency code for pricing (default: "USD").
            market (str): Market region code (default: "US").
            retry_delay (int): Seconds to wait between polling retries (default: 2).
            max_retries (int): Maximum number of polling retries (default: 15).
            proxies (dict): Proxy configuration for HTTP requests.
            px_authorization (str | None): Optional pre-generated PX authorization token.
            verify (bool): If set to False requests is not gonna verify the ssl certificate (default: True).

        Raises:
            None
        """
        if not px_authorization:
            solver = PXSolver(proxy=proxy,verify=verify)
            px_authorization, UUID = solver.gen_px_authorization()
        
        headers = {
            "X-Skyscanner-ChannelId": "goandroid",
            "X-Skyscanner-Currency": currency,
            "X-Skyscanner-Locale": locale,
            "X-Skyscanner-Market": market,
            "X-Skyscanner-Device": "Android-phone",
            "X-Skyscanner-Device-Class": "phone",
            "X-Skyscanner-Client-Type": "net.skyscanner.android.main",
            "X-Skyscanner-Client-Network-Type": "WIFI",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Px-Authorization": px_authorization,
            "X-PX-Os": "Android",
            "X-Px-Uuid": UUID,
            "X-Px-Mobile-Sdk-Version": "3.4.",
        }
        self.retry_delay = retry_delay
        self.market = market
        self.currency = currency
        self.locale = locale
        self.max_retries = max_retries
        self.session = curl_cffi.Session(
            headers=headers,
            ja3=config.JA3,
            extra_fp=config.EXTRA_FP,
            akamai=config.AKAMAI,
            proxy=proxy,
            verify=verify
        )
    @typechecked
    def get_flight_prices(
        self,
        origin: Airport,
        destination: Airport | SpecialTypes,
        depart_date: datetime.datetime | SpecialTypes | None = None,
        return_date: datetime.datetime | SpecialTypes | None = None,
        cabinClass: CabinClass = CabinClass.ECONOMY,
        adults: int = 1,
        childAges: list[int] = [],
    ) -> SkyscannerResponse:
        """
        Search for flight prices between two points.

        Args:
            origin (Airport): Origin airport object.
            destination (Airport | SpecialTypes): Destination airport or special search type.
            depart_date (datetime | SpecialTypes | None): Departure date or special enum (default: now).
            return_date (datetime | SpecialTypes | None): Return date or special enum (optional).
            cabinClass (CabinClass): Cabin class for travel (default: ECONOMY).
            adults (int): Number of adult passengers (max 8).
            childAges (list[int]): List of child ages (each 0–17, max 8 children).

        Returns:
            SkyscannerResponse: Parsed response containing pricing and itinerary data.

        Raises:
            ValueError: For invalid date logic or passenger counts.
            BannedWithCaptcha: If Skyscanner returns a CAPTCHA ban (403).
            AttemptsExhaustedIncompleteResponse: If polling exceeds retries without completion.
        """
        if not depart_date:
            depart_date = datetime.datetime.now()

        if not all(e >= 0 and e < 18 for e in childAges):
            raise ValueError("Child ages must be >= 0 and < 18")

        if isinstance(depart_date, datetime.datetime) and isinstance(
            return_date, datetime.datetime
        ):
            if return_date < depart_date:
                raise ValueError("Return date cannot be past departure")

        if not (adults <= 8 and len(childAges) <= 8):
            raise ValueError("Max 8 adults and 8 children")

        if {depart_date, return_date, destination} & {
            SpecialTypes.ANYTIME,
            SpecialTypes.EVERYWHERE,
        } and cabinClass != CabinClass.ECONOMY:
            raise ValueError(
                "To search for cabin class that's not economy enter depart_date / return_date and destination"
            )

        now = datetime.datetime.now()
        if depart_date < now or (return_date and (return_date < now)):
            raise ValueError("Depart date or return date cannot be in the past")

        json_data = {
            "adults": adults,
            "childAges": childAges,
            "cabinClass": cabinClass.value,
            "legs": [
                self.__gen_leg(depart_date, origin=origin, destination=destination),
            ],
            "options": None
        }

        if return_date:
            return_leg = self.__gen_leg(
                return_date, origin=destination, destination=origin
            )
            json_data["legs"].append(return_leg)

        custom_headers = {
            "X-Skyscanner-Viewid": str(uuid.uuid4()),
            "Content-Type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip, deflate, br"
        }
        req = self.session.post(config.UNIFIED_SEARCH_ENDPOINT, json=json_data, headers=custom_headers)
        if req.status_code == 403:
            raise BannedWithCaptcha(req.json()['url'])
        data = orjson.loads(req.content)


        if data["context"]["status"] == "complete":
            return SkyscannerResponse(
                data,
                session_id=self.__get_session_id(data),
                search_payload=json_data,
                origin=origin,
                destination=destination,
            )

        retries = 0
        session_id = data["context"]["sessionId"]

        while retries < self.max_retries:
            time.sleep(self.retry_delay)
            url = config.UNIFIED_SEARCH_ENDPOINT + session_id
            req = self.session.get(url, headers=custom_headers)
            data = orjson.loads(req.content)

            if req.status_code != 200:
                raise (
                    f"Error while scraping flight, status_code: {req.status_code} response: {req.text}"
                )

            if data["context"]["status"] == "complete":
                return SkyscannerResponse(
                    data,
                    session_id=self.__get_session_id(data),
                    search_payload=json_data,
                    origin=origin,
                    destination=destination,
                )
            session_id = data["context"]["sessionId"]
            retries += 1

        raise AttemptsExhaustedIncompleteResponse()
    
    @typechecked
    def search_airports(self, query: str, depart_date=None, return_date=None) -> list[Airport]:
        """
        Auto-suggest airports based on a query string.

        Args:
            query (str): Text to search for airport names or codes.
            depart_date (datetime | None): Optional outbound date for context.
            return_date (datetime | None): Optional inbound date for context.

        Returns:
            list[Airport]: List of suggested Airport objects.

        Raises:
            BannedWithCaptcha: If API responds with a CAPTCHA ban (403).
            GenericError: For non-200 status codes.
        """
        req = self.session.get(
            config.SEARCH_ORIGIN_ENDPOINT,
            params={
                "query": query,
                "inboundDate": depart_date.strftime("%Y-%m-%d") if depart_date else "",
                "outboundDate": return_date.strftime("%Y-%m-%d") if return_date else "",
            },
        )
        if req.status_code == 403:
            raise BannedWithCaptcha("https://www.skyscanner.net" + req.json()['redirect_to'])

        if req.status_code != 200:
            raise GenericError(f"Error when scraping airports, code: {req.status_code} text: {req.text}")

        data = req.json()
        return [
            Airport(
                title=e["presentation"]["title"],
                entity_id=e["navigation"]["entityId"],
                skyId=e["navigation"]["relevantFlightParams"]["skyId"],
            )
            for e in data["inputSuggest"]
        ]

    @typechecked
    def search_locations(self, query: str) -> list[Location]:
        """
        Auto-suggest locations based on a query.

        Args:
            query (str): Text to search for locations.

        Returns:
            list[Location]: List of suggested Location objects.

        Raises:
            BannedWithCaptcha: If API responds with a CAPTCHA ban (403).
            GenericError: For non-200 status codes.
        """
        url = config.LOCATION_SEARCH_ENDPOINT.format(locale=self.locale,market=self.market) + query
        params = {"autosuggestExp": "neighborhood_b"}

        req = self.session.get(url, params=params)
        if req.status_code == 403:
            raise BannedWithCaptcha("https://www.skyscanner.net" + req.json()['redirect_to'])

        if req.status_code != 200:
            raise GenericError(f"Error when scraping airports, code: {req.status_code} text: {req.text}")

        return [
            Location(location['entity_name'], location['entity_id'], location['location'])
            for location in req.json()
        ]

    @typechecked
    def get_airport_by_code(self, airport_code: str) -> Airport:
        """
        Retrieve a single Airport by its IATA code.

        Args:
            airport_code (str): Three-letter IATA code to look up.

        Returns:
            Airport: Matching Airport object.

        Raises:
            GenericError: If no airport matches the given code.
        """
        airports = self.search_airports(airport_code)
        for airport in airports:
            if airport.skyId == airport_code:
                return airport
        raise GenericError(f"IATA code not found: {airport_code}")
    
    @typechecked
    def get_itinerary_details(self, itineraryId: str, response: SkyscannerResponse) -> dict:
        """
        Retrieve detailed information for a specific flight itinerary.

        This method fetches extended itinerary data for a previously obtained search session and itinerary ID.

        Warning: itineraryId must be obtained from the SkyscannerResponse given

        Args:
            itineraryId (str): Unique identifier for the itinerary, obtained from SkyscannerResponse.
            response (SkyscannerResponse): The response object from a flight search containing session_id,
                search_payload, origin, and destination details.

        Returns:
            dict: Parsed JSON response with itinerary details including flight legs,
                user preferences, and search request parameters.

        Raises:
            BannedWithCaptcha: If Skyscanner returns a CAPTCHA ban (HTTP 403).
            GenericError: For non-200 HTTP responses indicating a failed request.

        Example:
            >>> details = scanner.get_itinerary_details(itinerary_id, search_response)
            >>> flight_legs = details.get('itineraryLegs')
        """
        json_data = {
            "itineraryId": itineraryId,
            "searchSessionId": response.session_id,
            "featuresEnabled": ["FEATURES_ENABLED_ITINERARY_LEGACY_INFO"],
            "userPreferences": {
                "market": self.market,
                "currencyCode": self.currency,
                "locale": self.locale,
            },
            "searchRequestDetails": {
                "adults": response.search_payload["adults"],

                "cabinClass": response.search_payload["cabinClass"],
                "legs": [],
            },
            "options": {
                "totalCostOptions": { 
                    "fareAttributeFilters": ["ATTRIBUTE_CABIN_BAGGAGE", "ATTRIBUTE_CHECKED_BAGGAGE"] 
                }
            }
        }
        if response.search_payload["childAges"]:
            json_data["searchRequestDetails"]['childAges'] = response.search_payload["childAges"]
        for leg in response.search_payload["legs"]:
            originId = leg.get("legOrigin", leg)['entityId']
            destinationId = leg.get("legDestination", leg)['entityId']
            originIata = (
                    response.origin.skyId # suf
                    if response.origin.entity_id == originId
                    else response.destination.skyId
                )
            destinationIata = (
                    response.destination.skyId
                    if response.destination.entity_id == destinationId
                    else response.origin.skyId
                )
            date = leg["dates"]
            res = {
                "originIata":originIata ,
                "destinationIata":destinationIata ,
                "date": {"year": date["year"], "month": date["month"], "day": date["day"]},
                "addAlternativeOrigins": False,
                "addAlternativeDestinations": False,
                "originSkyscannerCode": originIata,
                "destinationSkyscannerCode": destinationIata,
                "originEntityId": "",
                "destinationEntityId": ""
            }
            json_data["searchRequestDetails"]["legs"].append(res)
        headers = {
            "grpc-metadata-x-skyscanner-devicedetection-istablet": "false", # required 
            "grpc-metadata-x-skyscanner-devicedetection-ismobile": "true", # required
            "grpc-metadata-x-skyscanner-channelid": "goandroid",
            "grpc-metadata-x-skyscanner-viewid": str(uuid.uuid4()),
            "grpc-metadata-x-skyscanner-clientid": "skyscanner_app",
            "grpc-metadata-x-skyscanner-client-type": "net.skyscanner.android.main",
            "grpc-metadata-skyscanner-flights-config-session-id": str(uuid.uuid4()),
            "grpc-metadata-x-skyscanner-consent-information": "true",
            "grpc-metadata-x-skyscanner-consent-adverts": "true",
            "content-type": "application/json; charset=utf-8",
            "accept-encoding": "gzip",
        }
        req = self.session.post(config.ITINERARY_DETAILS_ENDPOINT, json=json_data, headers=headers)
        if req.status_code == 403:
            raise BannedWithCaptcha("https://www.skyscanner.net" + req.json().get('redirect_to', ''))
        if req.status_code != 200:
            raise GenericError(f"Error fetching itinerary details, code: {req.status_code}, text: {req.text}")

        return orjson.loads(req.content)
    
    @typechecked
    def get_car_rental_from_url(self, url : str):
        """
        Parses a car rental booking URL and returns car rental options based on the extracted parameters.

        The method extracts information such as driver's age, origin and destination location IDs, 
        departure and return times from a structured Skyscanner-style URL. It then uses these parameters 
        to fetch car rental data via `self.get_car_rental`.

        Example URL:
            https://www.skyscanner.net/g/carhire-quotes/GB/en-GB/GBP/30/27544008/27544008/2025-07-01T10:00/2025-08-01T10:00/?group=true...

        Parameters:
            url (str): A Skyscanner car hire URL containing rental booking information.

        Returns:
            Any: The result of the `get_car_rental` method, which provides car rental options.

        Raises:
            ValueError: If the date format is invalid or required segments are missing from the URL.
        """
            
        url = url.split("?")[0]

        args = url.split("/")
        
        if len(args) < 14:
            raise ValueError("URL not valid")

        is_driver_over_25 = int(args[8]) >= 25

        origin = Location("",args[9],"")
        destination = Location("",args[10],"")

        depart_time = datetime.datetime.fromisoformat(args[11])
        return_time = datetime.datetime.fromisoformat(args[12])
        print(origin,destination,depart_time,return_time,is_driver_over_25)
        return self.get_car_rental(
            origin=origin,
            depart_time=depart_time,
            return_time=return_time,
            is_driver_over_25=is_driver_over_25,
            destination=destination
        )

    @typechecked
    def get_car_rental(
        self,
        origin: Location | Coordinates | Airport,
        depart_time: datetime.datetime,
        return_time: datetime.datetime,
        destination: Location | Coordinates | Airport | None = None,
        is_driver_over_25: bool = True
    ) -> dict:
        """
        Search for car rental options between two locations and times.

        Args:
            origin (Location | Coordinates | Airport): Pickup location.
            depart_time (datetime): Pickup datetime.
            return_time (datetime): Drop-off datetime.
            destination (Location | Coordinates | Airport | None): Drop-off location (defaults to origin).
            is_driver_over_25 (bool): Flag for driver age pricing threshold

        Returns:
            dict: JSON response containing car rental group listings and metadata.

        Raises:
            ValueError: If dates are invalid or in the past.
            AttemptsExhaustedIncompleteResponse: If polling retries exhaust without stable response.
        """
        if not destination:
            destination = origin

        if return_time < depart_time:
            raise ValueError("Return time cannot be past depart time")

        now = datetime.datetime.now()
        if return_time < now or depart_time < now:
            raise ValueError("Return or depart time cannot be in the past")

        first_location = origin.entity_id if not isinstance(origin, Coordinates) else f"{origin.latitude},{origin.longitude}"
        second_location = destination.entity_id if not isinstance(destination, Coordinates) else f"{destination.latitude},{destination.longitude}"

        age_value = '30' if is_driver_over_25 else '21'

        first_date = depart_time.strftime("%Y-%m-%dT%H:%M")
        second_date = return_time.strftime("%Y-%m-%dT%H:%M")

        url = config.CAR_RENTAL_ENDPOINT.format(
            first_location=first_location,
            second_location=second_location,
            driver_age=age_value,
            first_date=first_date,
            second_date=second_date,
            market=self.market,
            currency=self.currency,
            locale=self.locale,
        )

        params = {
            'group': 'true',
            'sipp_map': 'true',
            'channel': 'android',
            'vndr_img_rounded': 'true',
            'ranking_enable': 'false',
            'reqn': '0',
            'version': '6.9',
            'include_location': 'true',
            'city_search_enable': 'true',
        }

        last_count = None

        for _ in range(self.max_retries):
            req = self.session.get(url, params=params)
            req_data = req.json()
            params['reqn'] = str(int(params['reqn']) + 1)

            count = req_data['groups_count']
            if not last_count:
                last_count = count
                time.sleep(self.retry_delay)
                continue

            if count == last_count:
                return req_data

            last_count = count
            time.sleep(self.retry_delay)

        raise AttemptsExhaustedIncompleteResponse()

    def __get_session_id(self, data: dict) -> str | None:
        """
        Extract the search session ID from a Skyscanner API response.

        Args:
            data (dict): JSON payload from a search request.

        Returns:
            str | None: Session ID string, or None if not present.
        """
        if "itineraries" not in data:
            return None
        return data["itineraries"]["context"]["sessionId"]

    def __gen_leg(
        self,
        depart_date: datetime.datetime | SpecialTypes | None = None,
        return_date: datetime.datetime | SpecialTypes | None = None,
        origin: Airport | SpecialTypes | None = None,
        destination: Airport | SpecialTypes | None = None
    ) -> dict:
        """
        Construct a search leg dictionary for Skyscanner API requests.

        Args:
            depart_date (datetime | SpecialTypes | None): Outbound date or enum.
            return_date (datetime | SpecialTypes | None): Inbound date or enum.
            origin (Airport | SpecialTypes | None): Origin airport or special enum.
            destination (Airport | SpecialTypes | None): Destination airport or special enum.

        Returns:
            dict: Formatted leg with dates, origin/destination entities, and placeOfStay.
        """
        res = {}
        date = depart_date if depart_date else return_date
        res["dates"] = (
            {"@type": "date", "year": date.year, "month": date.month, "day": date.day}
            if isinstance(date, datetime.datetime)
            else {"@type": date}
        )
        res["legOrigin"] = (
            {"@type": "entity", "entityId": origin.entity_id}
            if isinstance(origin, Airport)
            else {"@type": origin}
        )
        res["legDestination"] = (
            {"@type": "entity", "entityId": destination.entity_id}
            if isinstance(destination, Airport)
            else {"@type": destination}
        )
        res["placeOfStay"] = (
            destination.entity_id if isinstance(destination, Airport) else origin.entity_id
        )
        return res
