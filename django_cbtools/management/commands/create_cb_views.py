from django.core.management.base import BaseCommand

from django_cbtools.connection import connection


class Command(BaseCommand):

    def handle(self, *args, **options):
        from django.apps import apps
        for app_config in apps.get_app_configs():
            self.create_views_for_app(app_config)

    def create_views_for_app(self, app_config):
        import os
        file_directory = app_config.path + "/couchbase_views/"

        try:
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

            if views:
                connection().design_create(app_config.label, {"views": views})
                connection().design_publish(app_config.label)

                # print 'created %d views for %s: %s' % (len(views), app_config.label, views.keys())
        except:
            pass
