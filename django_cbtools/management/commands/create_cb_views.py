from django.core.management.base import BaseCommand
from django.conf import settings

from django_cbtools.connection import connection


class Command(BaseCommand):

    def handle(self, *args, **options):
        import os
        file_directory = os.path.realpath(settings.BASE_DIR + "/couchbase_views/")

        views = {}
        for filename in os.listdir(file_directory):
            if filename.endswith("_reduce.js"):
                continue

            if filename.endswith(".js"):
                f = open(file_directory + '/' + filename, 'r')
                # remove extension
                view_name = filename[:-3]
                view_content = f.read()
                views[view_name] = {"map": view_content}

                try:
                    reduce_filename = view_name + '_reduce.js'
                    reduce_file = open(file_directory + '/' + reduce_filename, 'r')
                    views[view_name]["reduce"] = reduce_file.read()
                except:
                    pass

        connection().design_create(settings.COUCHBASE_DESIGN, {"views": views})
        connection().design_publish(settings.COUCHBASE_DESIGN)
