import requests, ssl, socket, json
from urllib.parse import urlparse

def get_ssl_info(host, port=443):
    ctx = ssl.create_default_context()
    with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
        s.settimeout(5)
        s.connect((host, port))
        cert = s.getpeercert()
    return cert

def check_security_headers(url):
    try:
        r = requests.get(url, timeout=5)
        headers = r.headers
        missing = []
        for h in ["Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Strict-Transport-Security"]:
            if h not in headers:
                missing.append(h)
        return {"status_code": r.status_code, "missing_headers": missing}
    except Exception as e:
        return {"error": str(e)}

def scan(url):
    parsed = urlparse(url)
    host = parsed.hostname
    results = {"url": url}
    # SSL Certificate
    try:
        results["ssl_certificate"] = get_ssl_info(host)
    except Exception as e:
        results["ssl_error"] = str(e)
    # Security Headers
    results["headers"] = check_security_headers(url)
    return results

if __name__ == "__main__":
    target = "https://demo.testfire.net"
    report = scan(target)
    print(json.dumps(report, indent=2, default=str))
