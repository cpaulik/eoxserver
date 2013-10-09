#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------


from eoxserver.core import implements
from eoxserver.backends.cache import CacheContext
from eoxserver.contrib.mapserver import create_request, Map, Layer
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.mapserver.wms.util import MapServerWMSBaseComponent
from eoxserver.services.ows.wms.interfaces import (
    WMSLegendGraphicRendererInterface
)


class MapServerWMSLegendGraphicRenderer(MapServerWMSBaseComponent):
    """ A WMS feature info renderer using MapServer.
    """
    implements(WMSLegendGraphicRendererInterface)

    
    def render(self, layer_groups, request_values, **options):
        map_ = Map()
        map_.setMetaData("ows_enable_request", "*")
        map_.setProjection("EPSG:4326")

        with CacheContext() as cache:

            connector_to_layers = self.setup_map(
                layer_groups, map_, options, cache
            )

            request = create_request(request_values)

            try:
                response = map_.dispatch(request)
                return response.content, response.content_type
            finally:
                # cleanup
                for connector, items in connector_to_layers.items():
                    for coverage, data_items, layer in items:
                        connector.disconnect(coverage, data_items, layer, cache)