from account.forms import OrganizationMemberToGroupAddForm
from account.mixins import OrganizationPermissionRequiredMixin, OrganizationView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import CreateView
from django_otp.decorators import otp_required
from two_factor.views.utils import class_view_decorator

User = get_user_model()


@class_view_decorator(otp_required)
class OrganizationMemberAddView(OrganizationPermissionRequiredMixin, OrganizationView, CreateView):
    """
    View to create a new member for a specific organization.
    """

    model = User
    template_name = "organizations/organization_member_add.html"
    form_class = OrganizationMemberToGroupAddForm
    permission_required = "tools.add_organizationmember"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization_code"] = self.organization.code
        return kwargs

    def get_success_url(self, **kwargs):
        return reverse_lazy("organization_member_list", kwargs={"organization_code": self.organization.code})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {
                "url": reverse("organization_member_list", kwargs={"organization_code": self.organization.code}),
                "text": "Members",
            },
            {
                "url": reverse(
                    "organization_member_add",
                    kwargs={"organization_code": self.organization.code},
                ),
                "text": _("Add member"),
            },
        ]
        context["organization"] = self.organization

        return context

    def form_valid(self, form):
        self.add_success_notification()
        return super().form_valid(form)

    def add_success_notification(self):
        success_message = _("Member added successfully.")
        messages.add_message(self.request, messages.SUCCESS, success_message)
