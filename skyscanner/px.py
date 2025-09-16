import struct
from typing import List
import curl_cffi
import base64
import time
import uuid
import json
import hashlib
import secrets
import random
from .errors import PerimeterXError
from . import config

class ParseAppc:
    def __init__(self, appc: List[str]):
        """
        Initialize the ParseAppc class with a list of strings from the appc challenge.

        Args:
            appc (List[str]): The appc challenge data, must contain at least 10 elements.

        Raises:
            PerimeterXError: If the appc list contains fewer than 10 elements.
        """
        if len(appc) < 10:
            raise PerimeterXError("Cannot parse AppC challenge, must be at least 10")
        self.timestamp = int(appc[2])
        self.hash = appc[3]
        self.f24f = int(appc[4])
        self.f25g = int(appc[5])
        self.f21c = int(appc[6])
        self.f22d = int(appc[7])
        self.f23e = int(appc[8])
        self.f26h = int(appc[9])
    
    @staticmethod
    def a(i10: int, i11: int, i12: int, i13: int) -> int:
        """
        Perform a custom computation based on four integer inputs.

        Args:
            i10 (int): First input value.
            i11 (int): Second input value.
            i12 (int): Third input value.
            i13 (int): Fourth input value.

        Returns:
            int: Result of the custom computation.
        """
        i14 = i13 % 10
        i15 = i12 % i14 if i14 != 0 else i12 % 10
        i16 = i10 * i10
        i17 = i11 * i11
        
        if i15 == 0:
            return i16 + i11
        elif i15 == 1:
            return i10 + i17
        elif i15 == 2:
            return i16 * i11
        elif i15 == 3:
            return i10 ^ i11
        elif i15 == 4:
            return i10 - i17
        elif i15 == 5:
            i18 = i10 + 783
            return (i18 * i18) + i17
        elif i15 == 6:
            return (i10 ^ i11) + i11
        elif i15 == 7:
            return i16 - i17
        elif i15 == 8:
            return i10 * i11
        elif i15 == 9:
            return (i11 * i10) - i10
        else:
            return -1
    
    def encode(self, string1: str) -> int:
        """
        Encodes a given string using a derived integer value and XOR logic.

        Args:
            string1 (str): The input string to encode.

        Returns:
            int: Encoded integer result.
        """
        a10 = self.a(
            self.a(self.f21c, self.f22d, self.f24f, self.f26h),
            self.f23e, 
            self.f25g, 
            self.f26h
        )
        
        try:
            b_arr = string1.encode('utf-8')
        except:
            b_arr = bytearray(4)
        
        if len(b_arr) < 4:
            int_value = 0
        else:
            int_value = struct.unpack('>i', b_arr[:4])[0]
        
        return int_value ^ a10
      
class PXSolver:
    """
    A class to solve PerimeterX mobile challenges by generating a PX authorization token.
    """

    def __init__(self, device_data_dir = config.PX_DEVICE_DATA_DIR, proxy : str = '', verify : bool = True):
        """
        Initialize the PXSolver with device data path and proxy configuration.

        Args:
            device_data_dir (str): Path to the JSON file containing device fingerprints.
            proxies (dict): Optional proxy configuration.
            verify (bool): Whether to verify SSL certificates.
        """
        self.device_data_dir = device_data_dir

        headers = {
            'Host': 'collector-pxrf8vapwa.perimeterx.net',
            'User-Agent': 'PerimeterX Android SDK/3.4.4',
            'Accept-Charset': 'UTF-8',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
            'Connection': 'keep-alive',
        }

        self.session = curl_cffi.Session(headers=headers,ja3=config.JA3,akamai=config.AKAMAI,extra_fp=config.EXTRA_FP,proxy=proxy,verify=verify)


    def gen_px_authorization(self):
        """
        Generates a PX authorization token.

        Returns:
            str: A valid PX authorization string.
        """
        fingerprint = self.__get_fingerprint()
        auth, uuid = self.gen_px(fingerprint)
        return auth, uuid
    
    def __get_device_data(self):
        """
        Loads and caches device data from the device data directory.

        Returns:
            list: A list of device fingerprint dictionaries.
        """
        if hasattr(self,"_devicedata"):
            return self._devicedata
        with open(config.PX_DEVICE_DATA_DIR) as f:
            self._devicedata = json.load(f)
        return self._devicedata
    
    def __get_fingerprint(self):
        """
        Selects a random device fingerprint from the loaded device data.

        Returns:
            dict: A single device fingerprint dictionary.
        """
        return random.choice(self.__get_device_data())


    def gen_px(self, fingerprint):
        """
        Constructs and sends challenge payloads to the PerimeterX API to solve the challenge.

        Args:
            fingerprint (dict): A device fingerprint used to craft the payload.

        Returns:
            str: A PX authorization string in the format '3:<token>'.

        Raises:
            PerimeterXError: If any part of the challenge solving fails.
        """
        PX326 = str(uuid.uuid4())
        PX327 = PX326.split("-")[0].upper()
        battery_percentage = random.randrange(15,90)
        conn_type = random.choice(["WiFi","Mobile"])
        battery_status = random.choice(["charging","discharging","not charging"])

        fingeprint = [
            {
                "t": "PX315",
                "d": {
                    "PX330": "new_session",
                    "PX1214": secrets.token_hex(8),
                    "PX91": fingerprint['height'],
                    "PX92": fingerprint['width'],
                    "PX21215": random.randrange(150,255), 
                    "PX316": True,
                    "PX318": str(fingerprint['sdk_int']),
                    "PX319": fingerprint['os_version'],
                    "PX320": fingerprint['model'],
                    "PX339": fingerprint['brand'],
                    "PX321": fingerprint['build_device'],
                    "PX323": int(time.time()),
                    "PX322": "Android",
                    "PX337": True,
                    "PX336": True,
                    "PX335": True,
                    "PX334": True,
                    "PX333": True,
                    "PX331": True,
                    "PX332": True,
                    "PX421": "false",
                    "PX442": "false",
                    "PX21218": "[]",
                    "PX21217": "[]",
                    "PX21224": "true",
                    "PX21221": "true",
                    "PX317": conn_type,
                    "PX344": "Android",
                    "PX347": '["en_US"]',
                    "PX343": "Unknown",
                    "PX415": battery_percentage,
                    "PX413": "unknown",
                    "PX416": "" if battery_status != "charging" else random.choice(["USB","Wireless"]),
                    "PX414": battery_status,
                    "PX419": "",
                    "PX418": round(random.uniform(25.0, 35.0), 1),
                    "PX420": self.battery_percentage_to_voltage(battery_percentage),
                    "PX340": "v3.4.4",
                    "PX342": "7.146",
                    "PX341": '"Skyscanner"',
                    "PX348": "net.skyscanner.android.main",
                    "PX1159": False,
                    "PX345": 0,
                    "PX351": 0,
                    "PX326": PX326,
                    "PX327": PX327,
                    "PX328": hashlib.sha1(f"{fingerprint['model']}{PX326}{PX327}".encode()).hexdigest().upper(),
                    "PX1208": "[]",
                    "PX21219": "{}",
                },
            }
        ]

        payload = base64.b64encode(json.dumps(fingeprint).encode()).decode("utf-8")

        UUID = str(uuid.uuid4())

        data = f'payload={payload}&uuid={UUID}&appId=PXrf8vapwA&tag=mobile&ftag=22'

        first_req = self.session.post("https://collector-pxrf8vapwa.perimeterx.net/api/v1/collector/mobile",data=data)
        
        if first_req.status_code != 200:
            raise PerimeterXError(f"Error while posting first payload, code {first_req.status_code} message : {first_req.text}")
        
        data = first_req.json()['do']

        vid = None
        sid = None
        appc = None

        for row in data:
            args = row.split("|")
            if vid and sid and appc:
                break

            if args[0] == "sid":
                sid = args[1]
                continue
            if args[0] == "vid":
                vid = args[1]
                continue
            if args[0] == "appc" and len(args) >= 10:
                appc = args
                continue
        
        if not vid or not sid or not appc:
            raise PerimeterXError(f"Cannot find vid, sid or appc. Data : {data}")
        
        encoded_appc = ParseAppc(appc)
        fingeprint[0]['t'] = 'PX329'
        d = fingeprint[0]['d']
        
        d.pop("PX1208")
        d.pop("PX21219")

        d['PX259'] = encoded_appc.timestamp
        d['PX256'] = encoded_appc.hash
        d['PX257'] = str(encoded_appc.encode(fingerprint['model']))

        d['PX1208'] = '[]'
        d['PX21219'] = '{}'

        payload = base64.b64encode(json.dumps(fingeprint).encode()).decode("utf-8")
        data = f'payload={payload}&uuid={UUID}&appId=PXrf8vapwA&tag=mobile&ftag=22&sid={sid}&vid={vid}'

        first_req = self.session.post("https://collector-pxrf8vapwa.perimeterx.net/api/v1/collector/mobile",data=data)
        if first_req.status_code != 200:
            raise PerimeterXError(f"Error while posting second payload, code {first_req.status_code} message : {first_req.text}")
        

        data = first_req.json()['do']

        if len(data) != 1 or data[0].split("|")[0] != "bake":
            raise PerimeterXError(f"Error parsing PX response: {data}")
        
        args = data[0].split("|")

        return f"3:{args[3]}", UUID

    @staticmethod
    def battery_percentage_to_voltage(percentage: float) -> float:
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100.")
        if percentage <= 10:
            voltage = 3.0 + (percentage / 10) * 0.3   
        elif percentage <= 70:
            voltage = 3.3 + ((percentage - 10) / 60) * 0.6  
        else:
            voltage = 3.9 + ((percentage - 70) / 30) * 0.3 

        return round(voltage, 2)