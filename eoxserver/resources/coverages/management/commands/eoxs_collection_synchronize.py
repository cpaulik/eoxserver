#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from optparse import make_option
from itertools import product

from django.core.management.base import CommandError, BaseCommand

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.synchronization import synchronize
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--identifier", dest="collection_ids",
            action='callback', callback=_variable_args_cb,
            default=None, help=("Collection(s) from which the "
                                "objects shall be removed.")
        ),
    )

    args = (
        "<collection-id> [<collection-id> ...] "
    )

    help = """
        Synchronizes one or more collections and all their data sources.
    """


    @nested_commit_on_success
    def handle(self, *args, **kwargs):


        synchronize()



        # check the required inputs
        collection_ids = kwargs.get('collection_ids', None)
        remove_ids = kwargs.get('remove_ids', None)
        if not collection_ids: 
            raise CommandError(
                "Missing the mandatory collection identifier(s)!"
            )

        if not remove_ids: 
            raise CommandError(
                "Missing the mandatory identifier(s) for to be removed "
                "objects."
            )

        # extract the collections 
        ignore_missing_collection = kwargs['ignore_missing_collection']
        collections = [] 
        for collection_id in collection_ids: 
            try: 
                collections.append(
                    models.Collection.objects.get(identifier=collection_id)
                )
            except models.Collection.DoesNotExist: 
                msg = (
                    "There is no Collection matching the given "
                    "identifier: '%s'" % collection_id
                )
                if ignore_missing_collection: 
                    self.print_wrn(msg)
                else: 
                    raise CommandError(msg) 

        # extract the children  
        ignore_missing_object = kwargs['ignore_missing_object']
        objects = [] 
        for remove_id in remove_ids: 
            try:
                objects.append(
                    models.EOObject.objects.get(identifier=remove_id)
                )
            except models.EOObject.DoesNotExist:
                msg = (
                    "There is no EOObject matching the given identifier: '%s'"
                    % remove_id
                )
                if ignore_missing_object:
                    self.print_wrn(msg)
                else:
                    raise CommandError(msg)
        
        try:
            for collection, eo_object in product(collections, objects):
                # check whether the link does not exist
                if eo_object in collection:
                    self.print_msg(
                        "Unlinking: %s <-x- %s" % (collection, eo_object)
                    )
                    collection.remove(eo_object)

                else:
                    self.print_wrn(
                        "Collection %s does not contain %s" 
                        % (collection, eo_object)
                    )

        except Exception as e:
            self.print_traceback(e, kwargs)
            raise CommandError("Unlinking failed: %s" % (e))
