# -*- coding: utf-8 -*-
from Products.CMFPlone import PloneMessageFactory as _
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.users.schema import checkEmailAddress
from plone.autoform.form import AutoExtensibleForm
from plone.supermodel import model
from z3c.form import button
from z3c.form import form
from zope import schema


class IMemberSearchSchema(model.Schema):
    """Provide schema for member search."""

    model.fieldset(
        'extra',
        label=_(u'legend_member_search_criteria',
                default=u'User Search Criteria'),
        fields=['login', 'email', 'fullname']
    )

    login = schema.TextLine(
        title=_(u'label_name', default=u'Name'),
        description=_(
            u'help_search_name',
            default=u'Find users whose login name contain'),
        required=False,
    )
    email = schema.TextLine(
        title=_(u'label_email', default=u'E-mail'),
        description=_(
            u'help_search_email',
            default=u'Find users whose email address contain'),
        required=False,
    )
    fullname = schema.TextLine(
        title=_(u'label_fullname', default=u'Full Name'),
        description=_(
            u'help_search_fullname',
            default=u'Find users whose full names contain'),
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
    for key in ['_authenticator',
                'form.buttons.search',
                'form.widgets.roles-empty-marker', ]:
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


class MemberSearchForm(AutoExtensibleForm, form.Form):
    """This search form enables you to find users by specifying one or more
    search criteria.
    """

    schema = IMemberSearchSchema
    ignoreContext = True

    label = _(u'heading_member_search', default=u'Search for users')
    description = _(u'description_member_search',
                    default=u'This search form enables you to find users by '
                            u'specifying one or more search criteria.')
    template = ViewPageTemplateFile('membersearch_form.pt')
    enableCSRFProtection = True
    formErrorsMessage = _('There were errors.')

    submitted = False

    @button.buttonAndHandler(_(u'label_search', default=u'Search'),
                             name='search')
    def handleApply(self, action):
        request = self.request
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        if request.get('form.buttons.search', None):
            self.submitted = True

            view = self.context.restrictedTraverse('@@pas_search')
            criteria = extractCriteriaFromRequest(self.request.form.copy())
            self.results = view.searchUsers(sort_by=u'fullname', **criteria)
