from Acquisition import aq_inner
from Products.CMFPlone import PloneMessageFactory as _
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.users.browser.account import AccountPanelForm
from zope.component import getMultiAdapter
from z3c.form import button, form
from zope import schema
from zope.interface import Interface

from plone.autoform.form import AutoExtensibleForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from ..schema import checkEmailAddress

from plone.supermodel import model
from plone.autoform import directives
from z3c.form.browser.checkbox import CheckBoxWidget


class IMemberSearchSchema(model.Schema):

    """Provide schema for member search """

    login = schema.TextLine(
        title=_(u'label_name', default=u'Name'),
        description=_(
            u'help_search_name',
            default=u'Find users whose login names contain.'),
        required=False,
    )
    email = schema.TextLine(
        title=_(u'label_email', default=u'E-mail'),
        description=_(
            u'help_search_email',
            default=u'Find users whose email addresses contain.'),
        constraint=checkEmailAddress,
        required=False,
    )
    fullname = schema.TextLine(
        title=_(u'label_fullname', default=u'Full Name'),
        description=_(
            u'help_search_fullname',
            default=u'Return users with full names containing this value.'),
        required=False,
    )
    #directives.read_permission('roles', 'cmf.ManagePortal')
    #directives.write_permission('roles', 'cmf.ManagePortal')
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


def getView(context, request, name):
    # Remove the acquisition wrapper (prevent false context assumptions)
    context = aq_inner(context)
    # May raise ComponentLookUpError
    view = getMultiAdapter((context, request), name=name)
    # Add the view to the acquisition chain
    view = view.__of__(context)
    return view


class MemberSearchForm(AutoExtensibleForm, form.Form):

    """ This search form enables you to find users by specifying one or more
        search criteria.
    """

    schema = IMemberSearchSchema
    ignoreContext = True

    label = _(u'heading_member_search', default=u'Search for users')
    description = _(u'description_member_search', default=u"This search form \
        enables you to find users by specifying one or more search criteria.")
    template = ViewPageTemplateFile('membersearch_form.pt')
    enableCSRFProtection = True
    formErrorsMessage = _('There were errors.')

    def __init__(self, context, request):
        super(MemberSearchForm, self).__init__(context, request)
        self.submitted = False

    @button.buttonAndHandler(_(u'label_search', default=u'Search'), name='search')
    def handleApply(self, action):
        request = self.request
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        if request.get('form.buttons.search', None):
            self.submitted = True

            view = getView(self.context, request, 'pas_search')
            criteria = self.extractCriteriaFromRequest()
            self.results = view.searchUsers(sort_by='fullname', **criteria)

    def extractCriteriaFromRequest(self):
        criteria = self.request.form.copy()

        for key in ["_authenticator", "form.buttons.label_search"]:
            if key in criteria:
                del criteria[key]

        for (key, value) in criteria.items():
            if not value:
                del criteria[key]
            else:
                new_key = key.replace('form.widgets.', '')
                criteria[new_key] = value
                del criteria[key]

        return criteria
