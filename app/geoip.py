import ipaddress
from functools import lru_cache
from typing import Optional

import httpx

GEO_API_TIMEOUT_SECONDS = 3.0

_RFC1918_NETWORKS = [
    ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
]
_DOCUMENTATION_NETWORKS = [
    ipaddress.ip_network(n)
    for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")
]


class GeoResult:
    def __init__(
        self,
        ip: str,
        geolocatable: bool,
        reason: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ):
        self.ip = ip
        self.geolocatable = geolocatable
        self.reason = reason
        self.country = country
        self.city = city
        self.lat = lat
        self.lon = lon

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "geolocatable": self.geolocatable,
            "reason": self.reason,
            "country": self.country,
            "city": self.city,
            "lat": self.lat,
            "lon": self.lon,
        }


def _classify(addr) -> Optional[str]:
    if any(addr in net for net in _RFC1918_NETWORKS):
        return "Red privada (RFC 1918) - sin ubicación geográfica real"
    if any(addr in net for net in _DOCUMENTATION_NETWORKS):
        return "Rango reservado para documentación (RFC 5737) - no es una IP de internet real"
    if addr.is_loopback:
        return "Loopback (tu propia máquina) - sin ubicación geográfica real"
    if addr.is_link_local:
        return "Link-local - sin ubicación geográfica real"
    if not addr.is_global:
        return "IP no enrutable públicamente"
    return None


@lru_cache(maxsize=512)
def _fetch_geo(ip: str) -> GeoResult:
    ip = ip.split("/")[0]  # tolera "1.2.3.4/32" por si llega con sufijo CIDR
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return GeoResult(ip, geolocatable=False, reason="IP inválida")

    not_geolocatable_reason = _classify(addr)
    if not_geolocatable_reason:
        return GeoResult(ip, geolocatable=False, reason=not_geolocatable_reason)

    try:
        resp = httpx.get(
            f"http://ip-api.com/json/{ip}?fields=status,message,country,city,lat,lon",
            timeout=GEO_API_TIMEOUT_SECONDS,
        )
        data = resp.json()
        if data.get("status") != "success":
            return GeoResult(
                ip, geolocatable=False, reason=data.get("message", "Error del servicio de geolocalización")
            )

        return GeoResult(
            ip,
            geolocatable=True,
            country=data.get("country"),
            city=data.get("city"),
            lat=data.get("lat"),
            lon=data.get("lon"),
        )
    except (httpx.HTTPError, ValueError):
        return GeoResult(ip, geolocatable=False, reason="No se pudo contactar el servicio de geolocalización")


def geolocate(ip: str) -> dict:
    return _fetch_geo(ip).to_dict()
