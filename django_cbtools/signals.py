from django.db.models.signals import ModelSignal

cb_pre_save = ModelSignal(providing_args=["instance"], use_caching=True)
cb_post_save = ModelSignal(providing_args=["instance", "created"], use_caching=True)

cb_pre_delete = ModelSignal(providing_args=["instance"], use_caching=True)
cb_post_delete = ModelSignal(providing_args=["instance"], use_caching=True)
