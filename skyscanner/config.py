from pathlib import Path

MODULE_DIR = Path(__file__).parent


# TLS fingerprint

JA3 = '771,4865-4866-4867-49195-49196-52393-49199-49200-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-51-45-43-21,29-23-24,0'

AKAMAI = "4:16777216|16711681|0|m,p,a,s"

EXTRA_FP = {
    "tls_signature_algorithms": [
        "ecdsa_secp256r1_sha256",
        "rsa_pss_rsae_sha256",
        "rsa_pkcs1_sha256",
        "ecdsa_secp384r1_sha384",
        "rsa_pss_rsae_sha384",
        "rsa_pkcs1_sha384",
        "rsa_pss_rsae_sha512",
        "rsa_pkcs1_sha512",
        "rsa_pkcs1_sha1"
    ]
}

#Endpoints

UNIFIED_SEARCH_ENDPOINT = "https://www.skyscanner.net/g/radar/api/v2/unified-search/"
SEARCH_ORIGIN_ENDPOINT = "https://www.skyscanner.net/g/fenryr/v1/inputorigin"
ITINERARY_DETAILS_ENDPOINT = 'https://www.skyscanner.net/g/sonar/v3/itinerary/details'
LOCATION_SEARCH_ENDPOINT = 'https://www.skyscanner.net/g/autosuggest-search/api/v1/search-car/{market}/{locale}/'
CAR_RENTAL_ENDPOINT = 'https://www.skyscanner.net/g/carhire-quotes/{market}/{locale}/{currency}/{driver_age}/{first_location}/{second_location}/{first_date}/{second_date}'



PX_DEVICE_DATA_DIR = MODULE_DIR / "devicedata.json"

__author__ = "@irrisolto on discord"