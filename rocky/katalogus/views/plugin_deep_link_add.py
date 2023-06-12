from typing import Any, Dict

from account.mixins import OrganizationView
from django.contrib import messages
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.urls.base import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from katalogus.forms import PluginDeepLinkForm
from katalogus.models import OrganizationPlugin


class PluginDeepLinkCreateView(OrganizationView, CreateView):
    form_class = PluginDeepLinkForm
    template_name = "plugin_deep_link_add.html"
    permission_required = "katalogus.add_organizationplugin"

    def get_initial(self) -> Dict[str, Any]:
        initial = super().get_initial()
        if "ooi_type" in self.kwargs:
            initial["ooi_type"] = self.kwargs["ooi_type"]
        return initial

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        response = super().form_valid(form)
        OrganizationPlugin.objects.get_or_create(
            organization=self.organization, plugin=self.object, enabled=form.cleaned_data["enable"]
        )
        self.add_success_notification()
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("katalogus", kwargs={"organization_code": self.organization.code})

    def add_success_notification(self):
        success_message = _("Deep link successfully created.")
        messages.add_message(self.request, messages.SUCCESS, success_message)
