"""
Cisco Support API Client

Direct client for Cisco Support APIs using OAuth2 client credentials flow.
Provides access to Product, Bug, EoX, PSIRT, and Software APIs.
"""

import logging
import time
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CiscoSupportClient:
    """Client for Cisco Support APIs using OAuth2 authentication."""

    BASE_URL = "https://apix.cisco.com"
    TOKEN_URL = "https://id.cisco.com/oauth2/default/v1/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        timeout: int = 30,
        cache_timeout: int = 300,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.cache_timeout = cache_timeout
        self._token = None
        self._token_expiry = 0

    def _get_token(self) -> Optional[str]:
        """Get OAuth2 access token with caching."""
        cache_key = f"cisco_support_token_{self.client_id[:8]}"

        # Check Django cache first
        cached_token = cache.get(cache_key)
        if cached_token:
            return cached_token

        # Check instance cache
        if self._token and time.time() < self._token_expiry:
            return self._token

        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            self._token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)

            # Cache for slightly less than expiry time
            cache_duration = max(expires_in - 300, 60)
            self._token_expiry = time.time() + cache_duration
            cache.set(cache_key, self._token, cache_duration)

            logger.debug("Cisco API token obtained successfully")
            return self._token

        except requests.RequestException as e:
            logger.error(f"Failed to get Cisco API token: {e}")
            return None

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make authenticated request to Cisco API."""
        token = self._get_token()
        if not token:
            return {"error": "Failed to authenticate with Cisco API"}

        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )

            if response.status_code == 401:
                # Token expired, clear cache and retry once
                cache_key = f"cisco_support_token_{self.client_id[:8]}"
                cache.delete(cache_key)
                self._token = None
                self._token_expiry = 0

                token = self._get_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    response = requests.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=self.timeout,
                    )

            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            logger.error(f"Cisco API request timed out: {endpoint}")
            return {"error": "Request timed out"}
        except requests.RequestException as e:
            logger.error(f"Cisco API request failed: {e}")
            return {"error": str(e)}

    def get_product_info(self, serial_number: str) -> dict:
        """
        Get product information by serial number.

        API: GET /product/v1/information/serial_numbers/{serial_number}

        Returns product details including PID, name, series, category.
        """
        cache_key = f"cisco_product_{serial_number}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = f"/product/v1/information/serial_numbers/{serial_number}"
        result = self._make_request(endpoint)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_eox_by_serial(self, serial_number: str) -> dict:
        """
        Get End-of-Life information by serial number.

        API: GET /supporttools/eox/rest/5/EOXBySerialNumber/1/{serial_number}

        Returns EoX milestones (end of sale, end of support, etc.)
        """
        cache_key = f"cisco_eox_{serial_number}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = f"/supporttools/eox/rest/5/EOXBySerialNumber/1/{serial_number}"
        result = self._make_request(endpoint)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_eox_by_product(self, product_id: str) -> dict:
        """
        Get End-of-Life information by product ID.

        API: GET /supporttools/eox/rest/5/EOXByProductID/1/{product_id}

        Returns EoX milestones for the product.
        """
        cache_key = f"cisco_eox_pid_{product_id}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = f"/supporttools/eox/rest/5/EOXByProductID/1/{product_id}"
        result = self._make_request(endpoint)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_bugs_by_product(
        self,
        product_id: str,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page_index: int = 1,
    ) -> dict:
        """
        Get bugs for a product ID.

        API: GET /bug/v2.0/bugs/products/product_id/{product_id}

        Args:
            product_id: Cisco product ID (PID)
            severity: Filter by severity (1-6, comma-separated)
            status: Filter by status (O=Open, F=Fixed, T=Terminated)
            page_index: Page number for pagination

        Returns bugs array with bug_id, headline, severity, status.
        """
        cache_key = f"cisco_bugs_{product_id}_{severity}_{status}_{page_index}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = f"/bug/v2.0/bugs/products/product_id/{product_id}"
        params = {"page_index": page_index}
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status

        result = self._make_request(endpoint, params)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_bugs_by_product_and_version(
        self,
        product_id: str,
        software_version: str,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page_index: int = 1,
    ) -> dict:
        """
        Get bugs for a product ID and specific software version.

        API: GET /bug/v2.0/bugs/products/product_id/{product_id}/software_releases/{software_version}

        Args:
            product_id: Cisco product ID (PID) e.g., C9800-40-K9
            software_version: Software release version e.g., 17.9.5
            severity: Filter by severity (1-6, comma-separated)
            status: Filter by status (O=Open, F=Fixed, T=Terminated)
            page_index: Page number for pagination

        Returns bugs array with bug_id, headline, severity, status.
        """
        cache_key = f"cisco_bugs_ver_{product_id}_{software_version}_{severity}_{status}_{page_index}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = f"/bug/v2.0/bugs/products/product_id/{product_id}/software_releases/{software_version}"
        params = {"page_index": page_index}
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status

        result = self._make_request(endpoint, params)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_bugs_by_product_name_and_version(
        self,
        product_name: str,
        affected_release: str,
        modified_date: int = 5,
        severity: Optional[str] = None,
    ) -> dict:
        """
        Get bugs by product name and affected release version.

        API: GET /bug/v2.0/bugs/product_name/{product_name}/affected_releases/{version}

        Args:
            product_name: Full product name (e.g., "Cisco Catalyst 9300 Series Switches")
            affected_release: Software version (e.g., "17.9.5")
            modified_date: Modified within last N days (default 5)
            severity: Filter by severity (1-6, comma-separated)

        Returns bugs array with bug_id, headline, severity, status.
        """
        cache_key = f"cisco_bugs_name_{hash(product_name)}_{affected_release}_{modified_date}_{severity}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        # URL encode the product name for the path
        from urllib.parse import quote

        encoded_name = quote(product_name, safe="")
        endpoint = f"/bug/v2.0/bugs/product_name/{encoded_name}/affected_releases/{affected_release}"
        params = {"modified_date": modified_date}
        if severity:
            params["severity"] = severity

        result = self._make_request(endpoint, params)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_bugs_by_keyword(
        self,
        keyword: str,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page_index: int = 1,
    ) -> dict:
        """
        Get bugs by keyword search.

        API: GET /bug/v2.0/bugs/keyword/{keyword}

        Args:
            keyword: Search keyword (e.g., "C9300-48P")
            severity: Filter by severity (1-6, comma-separated)
            status: Filter by status (O=Open, F=Fixed, T=Terminated)
            page_index: Page number for pagination

        Returns bugs array with bug_id, headline, severity, status.
        """
        cache_key = f"cisco_bugs_kw_{keyword}_{severity}_{status}_{page_index}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = f"/bug/v2.0/bugs/keyword/{keyword}"
        params = {"page_index": page_index}
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status

        result = self._make_request(endpoint, params)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_psirt_by_product(self, product_id: str) -> dict:
        """
        Get PSIRT security advisories for a product.

        API: GET /security/advisories/v2/product?product={product_id}

        Returns advisories array with CVEs, severity, publication dates.
        """
        cache_key = f"cisco_psirt_{product_id}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = "/security/advisories/v2/product"
        params = {"product": product_id}
        result = self._make_request(endpoint, params)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_software_suggestions(self, product_id: str) -> dict:
        """
        Get software release suggestions for a product.

        API: GET /software/suggestion/v2/suggestions/software/productIds/{product_id}

        Returns suggested software versions and upgrade paths.
        """
        cache_key = f"cisco_software_{product_id}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = (
            f"/software/suggestion/v2/suggestions/software/productIds/{product_id}"
        )
        result = self._make_request(endpoint)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_coverage_status(self, serial_number: str) -> dict:
        """
        Get coverage status by serial number.

        API: GET /sn2info/v2/coverage/status/serial_numbers/{serial_number}

        Returns contract coverage status including warranty and service contract info.
        """
        cache_key = f"cisco_coverage_{serial_number}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = f"/sn2info/v2/coverage/status/serial_numbers/{serial_number}"
        result = self._make_request(endpoint)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def get_coverage_summary_bulk(self, serial_numbers: list) -> dict:
        """
        Get coverage summary for multiple serial numbers (e.g., switch stacks).

        API: GET /sn2info/v2/coverage/summary/serial_numbers/{sr_no,...}

        Args:
            serial_numbers: List of serial numbers (up to 75)

        Returns coverage summary for all serial numbers with is_covered, coverage_end_date, etc.
        """
        if not serial_numbers:
            return {"error": "No serial numbers provided"}

        # API supports up to 75 serial numbers
        serial_numbers = serial_numbers[:75]
        serials_str = ",".join(serial_numbers)

        cache_key = f"cisco_coverage_bulk_{hash(serials_str)}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        endpoint = f"/sn2info/v2/coverage/summary/serial_numbers/{serials_str}"
        result = self._make_request(endpoint)

        if "error" not in result:
            result["cached"] = False
            cache.set(cache_key, result, self.cache_timeout)

        return result

    def test_connection(self) -> dict:
        """Test API connectivity by attempting to get a token."""
        token = self._get_token()
        if token:
            return {"success": True, "message": "Successfully connected to Cisco API"}
        return {"success": False, "message": "Failed to authenticate with Cisco API"}


def get_client() -> Optional[CiscoSupportClient]:
    """
    Factory function to get a configured Cisco Support client.

    Returns None if credentials are not configured.
    """
    config = settings.PLUGINS_CONFIG.get("netbox_cisco_support", {})

    client_id = config.get("cisco_client_id")
    client_secret = config.get("cisco_client_secret")

    if not client_id or not client_secret:
        logger.warning("Cisco Support API credentials not configured")
        return None

    return CiscoSupportClient(
        client_id=client_id,
        client_secret=client_secret,
        timeout=config.get("timeout", 30),
        cache_timeout=config.get("cache_timeout", 300),
    )
