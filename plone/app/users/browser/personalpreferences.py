# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import getFSVersionTuple
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from z3c.form.interfaces import HIDDEN_MODE
from zope.interface import Interface
from zope.schema import Bool
from zope.schema import Choice

try:
    import plone.app.event  # nopep8
    HAS_PAE = True
except ImportError:
    HAS_PAE = False

try:
    import plone.app.vocabularies.datetimerelated  # nopep8
    HAS_DT_VOCAB = True
except ImportError:
    HAS_DT_VOCAB = False

PLONE5 = getFSVersionTuple()[0] >= 5


class IPersonalPreferences(Interface):
    """Provide schema for personalize form."""

    visible_ids = Bool(
        title=_(
            u'label_edit_short_names',
            default=u'Allow editing of Short Names'
        ),
        description=_(
            u'help_display_names',
            default=(u'Determines if Short Names (also known '
                     u'as IDs) are changable when editing items. If Short '
                     u'Names are not displayed, they will be generated '
                     u'automatically.')),
            required=False
    )

    wysiwyg_editor = Choice(
        title=_(u'label_wysiwyg_editor', default=u'Wysiwyg editor'),
        description=_(
            u'help_wysiwyg_editor',
            default=u'Wysiwyg editor to use.'
        ),
        vocabulary="plone.app.vocabularies.AvailableEditors",
        required=False,
    )

    ext_editor = Bool(
        title=_(u'label_ext_editor', default=u'Enable external editing'),
        description=_(
            u'help_content_ext_editor',
            default=u'When checked, an option will be made visible on each '
            'page which allows you to edit content with your favorite editor '
            'instead of using browser-based editors. This requires an '
            'additional application, most often ExternalEditor or '
            'ZopeEditManager, installed client-side. Ask your administrator '
            'for more information if needed.'
        ),
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
        """ Hide the visible_ids field based on portal_properties.
        """
        context = aq_inner(self.context)
        properties = getToolByName(context, 'portal_properties')
        siteProperties = properties.site_properties

        super(PersonalPreferencesPanel, self).updateWidgets()

        self.widgets['language'].noValueMessage = _(
            u"vocabulary-missing-single-value-for-edit",
            u"Language neutral (site default)"
        )
        self.widgets['wysiwyg_editor'].noValueMessage = _(
            u"vocabulary-available-editor-novalue",
            u"Use site default"
        )
        if not siteProperties.visible_ids:
            self.widgets['visible_ids'].mode = HIDDEN_MODE


class PersonalPreferencesConfiglet(PersonalPreferencesPanel):
    """Control panel version of the personal preferences panel"""
    template = ViewPageTemplateFile('account-configlet.pt')
