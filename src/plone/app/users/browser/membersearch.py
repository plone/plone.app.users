from plone.autoform.form import AutoExtensibleForm
from plone.base import PloneMessageFactory as _
from plone.memoize.view import memoize
from plone.supermodel import model
from Products.CMFCore.permissions import ListPortalMembers
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button
from z3c.form import form
from zope import schema


class IMemberSearchSchema(model.Schema):
    """Provide schema for member search."""

    model.fieldset(
        "extra",
        label=_("legend_member_search_criteria", default="User Search Criteria"),
        fields=["login", "email", "fullname"],
    )

    login = schema.TextLine(
        title=_("label_name", default="Name"),
        description=_(
            "help_search_name", default="Find users whose login name contain"
        ),
        required=False,
    )
    email = schema.TextLine(
        title=_("label_email", default="Email"),
        description=_(
            "help_search_email", default="Find users whose email address contain"
        ),
        required=False,
    )
    fullname = schema.TextLine(
        title=_("label_fullname", default="Full Name"),
        description=_(
            "help_search_fullname", default="Find users whose full names contain"
        ),
        required=False,
    )
    # disabled: https://dev.plone.org/ticket/13862
    """
    directives.read_permission(roles='cmf.ManagePortal')
    directives.write_permission(roles='cmf.ManagePortal')
    directives.widget('roles', CheckBoxWidget)
    roles = schema.List(
        title=_(u'label_roles', default=u'Role(s)'),
        description=_(
            u'help_search_roles',
            default=u'Find users with all of the selected roles.'),
        required=False,
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Roles',
        ),
    )
    """


def extractCriteriaFromRequest(criteria):
    """Takes a dictionary of z3c.form data and sanitizes it to fit
    for a pas member search.
    """
    for key in [
        "_authenticator",
        "form.buttons.search",
        "form.widgets.roles-empty-marker",
    ]:
        if key in criteria:
            del criteria[key]
    for key, value in list(criteria.items()):
        if not value:
            del criteria[key]
        else:
            new_key = key.replace("form.widgets.", "")
            criteria[new_key] = value
            del criteria[key]

    return criteria


class MemberSearchForm(AutoExtensibleForm, form.Form):
    """This search form enables you to find users by specifying one or more
    search criteria.
    """

    schema = IMemberSearchSchema
    ignoreContext = True

    label = _("heading_member_search", default="Search for users")
    description = _(
        "description_member_search",
        default="This search form enables you to find users by "
        "specifying one or more search criteria.",
    )
    template = ViewPageTemplateFile("membersearch_form.pt")
    enableCSRFProtection = True
    formErrorsMessage = _("There were errors.")

    submitted = False

    @property
    @memoize
    def listing_allowed(self):
        """
        Check if the user has the necessary "List Portal Members" permissions
        to view the list of search results.
        """
        pm = getToolByName(self.context, "portal_membership")
        return pm.checkPermission(ListPortalMembers, self.context)

    @property
    def results(self):
        """
        Retrieve, merge, and sort the list of results based on search criteria.

        This is based on the methods previously defined in the
        Products.PlonePAS.browser.search module.
        """
        # First of all check if we have the proper permissions
        if not self.listing_allowed:
            return []

        view = self.context.restrictedTraverse("@@pas_search")
        criteria = extractCriteriaFromRequest(self.request.form.copy())
        return view.searchUsers(sort_by="fullname", **criteria)

    @button.buttonAndHandler(_("label_search", default="Search"), name="search")
    def handleApply(self, action):
        request = self.request
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        if request.get("form.buttons.search", None):
            self.submitted = True
