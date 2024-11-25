"""API client for AppWash."""
from typing import Dict, Any, Optional
import aiohttp
import async_timeout

class AppWashAPI:
    """AppWash API client."""
    BASE_URL = "https://www.involtum-services.com/api-rest"
    
    def __init__(self, email: str, password: str) -> None:
        """Initialize the API client."""
        self._email = email
        self._password = password
        self._token: Optional[str] = None
        self._location_id: Optional[str] = None
        self._session = aiohttp.ClientSession()

    async def async_login(self) -> None:
        """Login to AppWash."""
        endpoint = "/login"
        payload = {"email": self._email, "password": self._password}
        
        async with async_timeout.timeout(10):
            async with self._session.post(
                f"{self.BASE_URL}{endpoint}",
                json=payload,
                headers=self._get_headers()
            ) as response:
                data = await response.json()
                
                if data.get("errorCode") == 0:
                    self._token = data["login"]["token"]
                else:
                    raise Exception(f"Login failed: {data.get('errorDescription')}")

    async def async_get_washing_machines(self) -> Dict[str, Any]:
        """Get washing machine data and calculate statistics."""
        if not self._location_id:
            await self._async_get_location()
            
        endpoint = f"/location/{self._location_id}/connectorsv2"
        payload = {"serviceType": "WASHING_MACHINE"}
        
        async with async_timeout.timeout(10):
            async with self._session.post(
                f"{self.BASE_URL}{endpoint}",
                json=payload,
                headers=self._get_headers()
            ) as response:
                response_data = await response.json()
                
                if response_data.get("errorCode") == 0:
                    machines_data = response_data["data"]
                    
                    # Initialize counters
                    available_machines = 0
                    occupied_machines = 0
                    machines_status = {}
                    
                    # Process each machine
                    for machine in machines_data:
                        connector_name = machine["connectorName"]
                        state = machine["state"]
                        
                        # Store machine state
                        machines_status[connector_name] = state
                        
                        # Count states
                        if state == "AVAILABLE":
                            available_machines += 1
                        elif state == "OCCUPIED":
                            occupied_machines += 1
                    
                    return {
                        "machines_status": machines_status,
                        "available_machines": available_machines,
                        "occupied_machines": occupied_machines,
                        "total_machines": len(machines_data),
                        "machines_data": machines_data
                        
                    }
                
                raise Exception(f"API request failed: {response_data.get('errorDescription', 'Unknown error')}")


    async def async_get_dryers(self) -> Dict[str, Any]:
        """Retrieves data about the dryers."""
        if not self._location_id:
            await self._async_get_location()
            
        endpoint = f"/location/{self._location_id}/connectorsv2"
        payload = {"serviceType": "DRYER"}

        async with async_timeout.timeout(10):
            async with self._session.post(
                f"{self.BASE_URL}{endpoint}",
                json=payload,
                headers=self._get_headers()
            ) as response:
                data = await response.json()
                
                if data.get("errorCode") == 0:
                    # Initialize variables for Home Assistant
                    available_dryers = 0
                    occupied_dryers = 0
                    dryers_status = {}    # Dictionary to store dryer states
                    dryers_data = []      # List to store all dryer data

                    # Iterate through all dryers in the response
                    for dryer in data["data"]:
                        connector_name = dryer["connectorName"]
                        state = dryer["state"]
                        
                        # Store dryer state in dictionary
                        dryers_status[connector_name] = state
                        
                        # Store complete dryer data
                        dryers_data.append({
                            "connectorName": connector_name,
                            "state": state
                        })

                        # Count available and occupied dryers
                        if state == "AVAILABLE":
                            available_dryers += 1
                        elif state == "OCCUPIED":
                            occupied_dryers += 1

                    # Return the data for Home Assistant
                    return {
                        "dryers_status": dryers_status,
                        "available_dryers": available_dryers,
                        "occupied_dryers": occupied_dryers,
                        "dryers_data": dryers_data
                    }

                else:
                    raise Exception(f"Dryer request failed: {data.get('errorDescription')}")


    async def async_get_balance(self) -> float:
        """Get account balance."""
        endpoint = "/account/getprepaid"
        
        async with async_timeout.timeout(10):
            async with self._session.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self._get_headers()
            ) as response:
                data = await response.json()
                return data["balanceCents"] / 100

    async def _async_get_location(self) -> None:
        """Get location ID."""
        endpoint = "/subscription"
        
        async with async_timeout.timeout(10):
            async with self._session.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self._get_headers()
            ) as response:
                data = await response.json()
                self._location_id = data["data"]["locationExternalId"]

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "platform": "appWash",
            "language": "EN",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "content-type": "application/json; charset=utf-8"
        }
        
        if self._token:
            headers["token"] = self._token
            
        return headers

    async def close(self) -> None:
        """Close the session."""
        await self._session.close()
