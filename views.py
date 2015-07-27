import logging

from django.http import HttpResponseRedirect, Http404
from django.views.generic import UpdateView, CreateView, DeleteView, ListView, DetailView, FormView
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class SingleObjectMixin(object):

    def get_object(self):
        current_account = CBAccount.get_current(self.request)

        """
        Returns the object the view is displaying.
        By default this requires  a `pk`  argument
        in the URLconf, but subclasses can override this to return any object.
        """

        try:
            pk = self.kwargs.get(self.pk_url_kwarg, None)
        except:
            pk = self.kwargs.get('pk', None)

        if pk is not None:
            object = self.model(pk)
            if set(current_account.channels).intersection(object.channels) and self.model.doc_type == object.doc_type:
                return object
            elif self.model == CBSmartTradeRecord and self.account.uid == object.partner_uid:
                return object
            else:
                raise Http404
        else:
            raise AttributeError("Generic detail view %s must be called with "
                                 "either an object pk ."
                                 % self.__class__.__name__)


class ExtraDataMixin(object):

    def get_extra_data(self):
        '''
        Override this function if you want to set extra data to your model.
        This is useful when the form does not have all the data needed
        '''
        return {}


class FormValidMixin(object):

    def form_valid(self, form):

        """
        If the form is valid, save the associated model.
        """
        try:
            pk = self.kwargs.get(self.pk_url_kwarg, None)
        except:
            pk = self.kwargs.get('pk', None)

        # update view or create view (if or else)
        if pk is not None:
            self.object = self.get_object()
        else:
            self.object = self.model()

        cleaned_data = form.clean()
        cleaned_data.update(self.get_extra_data())

        self.object.from_dict(cleaned_data)
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())


class CBListView(ListView):

    def get_queryset(self):
        """
        Return the list of items for this view.
        The return value must be an iterable
        """

        if self.queryset is not None:
            queryset = self.queryset
        elif self.model is not None:
            queryset = self.model.get_list(self.request)
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {
                    'cls': self.__class__.__name__
                }
            )
        return queryset


class CBDetailView(SingleObjectMixin,
                   DetailView):
    pass


class CBDeleteView(SingleObjectMixin,
                   DeleteView):

    pass


class CBUpdateView(SingleObjectMixin,
                   ExtraDataMixin,
                   FormValidMixin,
                   UpdateView):

    pass


class CBCreateView(ExtraDataMixin,
                   FormValidMixin,
                   CreateView):

    pass


class CBFormView(SingleObjectMixin,
                 ExtraDataMixin,
                 FormView):

    pass
