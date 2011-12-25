from collections import namedtuple
MinMax = namedtuple("MinMax", ("min", "max"))
LatLng = namedtuple("LatLng", ("lat", "lng"))
GeoRangeNT = namedtuple("GeoRangeNT", ("lat_min", "lat_max", "lng_min", "lng_max"))

__all__ = ('GeoRange')

class GeoRange(GeoRangeNT):
    @property
    def lat(self):
        return MinMax(self.lat_min, self.lat_max)
    @property
    def lng(self):
        return MinMax(self.lng_min, self.lng_max)
    @property
    def min(self):
        return LatLng(self.lat_min, self.lng_min)
    @property
    def max(self):
        return LatLng(self.lat_max, self.lng_max)

