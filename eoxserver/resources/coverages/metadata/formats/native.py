from lxml import etree
from lxml.builder import E

from django.utils.dateparse import parse_datetime
from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.util.xmltools import parse
from eoxserver.core.util.timetools import isoformat
from eoxserver.core.util.iteratortools import pairwise
from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface, MetadataWriterInterface
)


class NativeFormat(Component):
    implements(MetadataReaderInterface)
    implements(MetadataWriterInterface)

    formats = ("native", )

    def test(self, obj):
        xml = parse(obj)
        return xml is not None and xml.tag == "Metadata"


    def read(self, obj):
        tree = parse(obj)
        if tree is not None:
            decoder = NativeFormatDecoder(tree)
            return {
                "identifier": decoder.identifier,
                "begin_time": decoder.begin_time,
                "end_time": decoder.end_time,
                "footprint": MultiPolygon(*decoder.polygons)
            }
        raise Exception("Could not parse from obj '%s'." % repr(obj))


    def write(self, values, file_obj, format=None, encoding=None, pretty=False):
        def flip(point):
            return point[1], point[0]

        # ignore format
        tree = E.Metadata(
            E.EOID(values["identifier"]),
            E.BeginTime(isoformat(values["begin_time"])),
            E.EndTime(isoformat(values["end_time"])),
            E.Footprint(
                *map(lambda polygon: 
                    E.Polygon(
                        E.Exterior(
                            " ".join([
                                "%f %f" % flip(point)
                                for point in polygon.exterior_ring
                            ])
                        ),
                        *[E.Interior(
                            " ".join([
                                "%f %f" % flip(point)
                                for point in interior
                            ])
                        ) for interior in polygon[1:]]
                    ),
                    values["footprint"]
                )
            )
        )

        file_obj.write(
            etree.tostring(tree, pretty_print=pretty, encoding=encoding)
        )


def parse_polygon_xml(elem):
    return Polygon(
        parse_ring(elem.findtext("Exterior")),
        *map(lambda e: parse_ring(e.text), elem.findall("Interior"))
    )

def parse_ring(string):
    points = []
    raw_coords = map(float, string.split(" "))
    return [(lon, lat) for lat, lon in pairwise(raw_coords)]


class NativeFormatDecoder(xml.Decoder):
    identifier = xml.Parameter("EOID/text()")
    begin_time = xml.Parameter("BeginTime/text()", type=parse_datetime)
    end_time = xml.Parameter("EndTime/text()", type=parse_datetime)
    polygons = xml.Parameter("Footprint/Polygon", type=parse_polygon_xml, num="+")
