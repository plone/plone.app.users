# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import getFSVersionTuple
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from zope.interface import Interface
from zope.schema import Choice

try:
    import plone.app.event  # noqa
    HAS_PAE = True
except ImportError:
    HAS_PAE = False

try:
    import plone.app.vocabularies.datetimerelated  # noqa
    HAS_DT_VOCAB = True
except ImportError:
    HAS_DT_VOCAB = False

PLONE5 = getFSVersionTuple()[0] >= 5


class IPersonalPreferences(Interface):
    """Provide schema for personalize form."""

    wysiwyg_editor = Choice(
        title=_(u'label_wysiwyg_editor', default=u'Wysiwyg editor'),
        description=_(
            u'help_wysiwyg_editor',
            default=u'Wysiwyg editor to use.'
        ),
        vocabulary="plone.app.vocabularies.AvailableEditors",
        required=False,
    )

    language = Choice(
        title=_(u'label_language', default=u'Language'),
        description=_(u'help_preferred_language', u'Your preferred language.'),
        vocabulary="plone.app.vocabularies.AvailableContentLanguages",
        required=False
    )

    if HAS_PAE and HAS_DT_VOCAB:
        timezone = Choice(
            title=_(u'label_timezone', default=u'Time zone'),
            description=_(u'help_timezone', default=u'Your time zone'),
            vocabulary='plone.app.vocabularies.AvailableTimezones',
            required=False,
        )
    elif HAS_PAE:
        timezone = Choice(
            title=_(u'label_timezone', default=u'Time zone'),
            description=_(u'help_timezone', default=u'Your time zone'),
            vocabulary='plone.app.vocabularies.Timezones',
            required=False,
        )


class PersonalPreferencesPanelAdapter(AccountPanelSchemaAdapter):
    schema = IPersonalPreferences


class PersonalPreferencesPanel(AccountPanelForm):
    """Implementation of personalize form that uses z3c.form."""

    form_name = _(u'legend_personal_details', u'Personal Details')
    schema = IPersonalPreferences

    @property
    def description(self):
        userid = self.request.form.get('userid')
        mt = getToolByName(self.context, 'portal_membership')
        if userid and (userid != mt.getAuthenticatedMember().getId()):
            # editing someone else's profile
            return _(
                u'description_preferences_form_otheruser',
                default='Personal settings for $name',
                mapping={'name': userid}
            )
        else:
            # editing my own profile
            return _(
                u'description_my_preferences',
                default='Your personal settings.'
            )

    def updateWidgets(self):
        super(PersonalPreferencesPanel, self).updateWidgets()

        self.widgets['language'].noValueMessage = _(
            u"vocabulary-missing-single-value-for-edit",
            u"Language neutral (site default)"
        )
        self.widgets['wysiwyg_editor'].noValueMessage = _(
            u"vocabulary-available-editor-novalue",
            u"Use site default"
        )

    def __call__(self):
        self.request.set('disable_border', 1)
        return super(PersonalPreferencesPanel, self).__call__()


class PersonalPreferencesConfiglet(PersonalPreferencesPanel):
    """Control panel version of the personal preferences panel"""
    template = ViewPageTemplateFile('account-configlet.pt')
