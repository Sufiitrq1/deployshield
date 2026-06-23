import time
import logging
import http.client
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeployShield.SmokeTester")

def run_smoke_test(url: str, max_retries: int = 3, retry_interval: int = 5) -> tuple[bool, int, str]:
    """
    Executes live HTTP GET verification requests against the target application endpoint.
    Returns: (success_boolean, HTTP_status_code, status_message)
    """
    logger.info(f"Targeting smoke test verification at: {url}")
    parsed_url = urlparse(url)
    
    # Extract host, port, and path for http.client usage
    host = parsed_url.netloc
    path = parsed_url.path if parsed_url.path else "/"
    if parsed_url.query:
        path += f"?{parsed_url.query}"
        
    use_ssl = parsed_url.scheme == "https"

    for attempt in range(1, max_retries + 1):
        try:
            # Select connection client based on URL protocol scheme
            if use_ssl:
                conn = http.client.HTTPSConnection(host, timeout=5)
            else:
                conn = http.client.HTTPConnection(host, timeout=5)
                
            conn.request("GET", path)
            response = conn.getresponse()
            status = response.status
            reason = response.reason
            conn.close()
            
            logger.info(f"Smoke check run #{attempt}: HTTP status returned -> {status}")
            
            # Treat HTTP 200-299 as fully healthy states
            if 200 <= status < 300:
                return True, status, reason
                
        except Exception as e:
            logger.warning(f"Smoke check run #{attempt} connection failure: {str(e)}")
            status = 0
            reason = str(e)
            
        if attempt < max_retries:
            time.sleep(retry_interval)
            
    logger.error(f"Smoke testing permanently failed after {max_retries} attempts.")
    return False, status, reason