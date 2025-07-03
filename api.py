"""API client for AppWash."""
from typing import Dict, Any, Optional
import aiohttp
import asyncio

class AppWashAPI:
    """AppWash API client."""
    BASE_URL = "https://www.involtum-services.com/api-rest"
    
    def __init__(self, email: str, password: str) -> None:
        """Initialize the API client."""
        self._email = email
        self._password = password
        self._token: Optional[str] = None
        self._location_id: Optional[str] = None
        self._location_cached = False  # Add caching flag to prevent redundant lookups
        # Optimize session with connection pooling and keep-alive
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=10, keepalive_timeout=30),
            timeout=aiohttp.ClientTimeout(total=10)
        )

    async def async_login(self) -> None:
        """Login to AppWash."""
        endpoint = "/login"
        payload = {"email": self._email, "password": self._password}
        
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

    async def _ensure_location(self) -> None:
        """Ensure location ID is available, fetch only if needed."""
        if not self._location_cached:
            await self._async_get_location()
            self._location_cached = True

    async def async_get_washing_machines(self) -> Dict[str, Any]:
        """Get washing machine data and calculate statistics."""
        await self._ensure_location()
            
        endpoint = f"/location/{self._location_id}/connectorsv2"
        payload = {"serviceType": "WASHING_MACHINE"}
        
        async with self._session.post(
            f"{self.BASE_URL}{endpoint}",
            json=payload,
            headers=self._get_headers()
        ) as response:
            response_data = await response.json()
            
            if response_data.get("errorCode") == 0:
                machines_data = response_data["data"]
                
                # Optimize data structure - only store essential information
                machines_status = {}
                state_counts = {"AVAILABLE": 0, "OCCUPIED": 0, "OTHER": 0}
                
                # Process each machine efficiently
                for machine in machines_data:
                    connector_name = machine["connectorName"]
                    state = machine["state"]
                    
                    # Store machine state
                    machines_status[connector_name] = state
                    
                    # Count states efficiently
                    if state in state_counts:
                        state_counts[state] += 1
                    else:
                        state_counts["OTHER"] += 1
                
                return {
                    "machines_status": machines_status,
                    "available_machines": state_counts["AVAILABLE"],
                    "occupied_machines": state_counts["OCCUPIED"],
                    "total_machines": len(machines_data)
                    # Removed machines_data to reduce memory usage
                }
            
            raise Exception(f"API request failed: {response_data.get('errorDescription', 'Unknown error')}")

    async def async_get_dryers(self) -> Dict[str, Any]:
        """Retrieves data about the dryers."""
        await self._ensure_location()
            
        endpoint = f"/location/{self._location_id}/connectorsv2"
        payload = {"serviceType": "DRYER"}

        async with self._session.post(
            f"{self.BASE_URL}{endpoint}",
            json=payload,
            headers=self._get_headers()
        ) as response:
            data = await response.json()
            
            if data.get("errorCode") == 0:
                # Optimize data structure for better performance
                dryers_status = {}
                state_counts = {"AVAILABLE": 0, "OCCUPIED": 0, "OTHER": 0}

                # Iterate through all dryers efficiently
                for dryer in data["data"]:
                    connector_name = dryer["connectorName"]
                    state = dryer["state"]
                    
                    # Store dryer state in dictionary
                    dryers_status[connector_name] = state

                    # Count available and occupied dryers efficiently
                    if state in state_counts:
                        state_counts[state] += 1
                    else:
                        state_counts["OTHER"] += 1

                # Return optimized data structure
                return {
                    "dryers_status": dryers_status,
                    "available_dryers": state_counts["AVAILABLE"],
                    "occupied_dryers": state_counts["OCCUPIED"],
                    "total_dryers": len(data["data"])
                    # Removed dryers_data to reduce memory usage
                }

            else:
                raise Exception(f"Dryer request failed: {data.get('errorDescription')}")

    async def async_get_balance(self) -> float:
        """Get account balance."""
        endpoint = "/account/getprepaid"
        
        async with self._session.get(
            f"{self.BASE_URL}{endpoint}",
            headers=self._get_headers()
        ) as response:
            data = await response.json()
            return data["balanceCents"] / 100

    async def _async_get_location(self) -> None:
        """Get location ID."""
        endpoint = "/subscription"
        
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
