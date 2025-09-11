from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.base import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
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


class IPersonalPreferences(Interface):
    """Provide schema for personalize form."""

    wysiwyg_editor = Choice(
        title=_("label_wysiwyg_editor", default="Wysiwyg editor"),
        description=_("help_wysiwyg_editor", default="Wysiwyg editor to use."),
        vocabulary="plone.app.vocabularies.AvailableEditors",
        required=False,
    )

    language = Choice(
        title=_("label_language", default="Language"),
        description=_("help_preferred_language", "Your preferred language."),
        vocabulary="plone.app.vocabularies.AvailableContentLanguages",
        required=False,
    )

    if HAS_PAE and HAS_DT_VOCAB:
        timezone = Choice(
            title=_("label_timezone", default="Time zone"),
            description=_("help_timezone", default="Your time zone"),
            vocabulary="plone.app.vocabularies.AvailableTimezones",
            required=False,
        )
    elif HAS_PAE:
        timezone = Choice(
            title=_("label_timezone", default="Time zone"),
            description=_("help_timezone", default="Your time zone"),
            vocabulary="plone.app.vocabularies.Timezones",
            required=False,
        )


class PersonalPreferencesPanelAdapter(AccountPanelSchemaAdapter):
    schema = IPersonalPreferences


class PersonalPreferencesPanel(AccountPanelForm):
    """Implementation of personalize form that uses z3c.form."""

    form_name = _("legend_personal_details", "Personal Details")
    schema = IPersonalPreferences

    @property
    def description(self):
        userid = self.request.form.get("userid")
        mt = getToolByName(self.context, "portal_membership")
        if userid and (userid != mt.getAuthenticatedMember().getId()):
            # editing someone else's profile
            return _(
                "description_preferences_form_otheruser",
                default="Personal settings for $name",
                mapping={"name": userid},
            )
        else:
            # editing my own profile
            return _("description_my_preferences", default="Your personal settings.")

    def updateWidgets(self):
        super().updateWidgets()

        self.widgets["language"].noValueMessage = _(
            "vocabulary-missing-single-value-for-edit",
            "Language neutral (site default)",
        )
        self.widgets["wysiwyg_editor"].noValueMessage = _(
            "vocabulary-available-editor-novalue", "Use site default"
        )

    def __call__(self):
        self.request.set("disable_border", 1)
        return super().__call__()


class PersonalPreferencesConfiglet(PersonalPreferencesPanel):
    """Control panel version of the personal preferences panel"""

    template = ViewPageTemplateFile("account-configlet.pt")
    tab = "userprefs"
