from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.base import PloneMessageFactory as _
from zope.interface import Interface
from zope.schema import Choice

import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.passwordpanel import PersonalPreferencesPanel instead.",
    PersonalPreferencesPanel="plone.app.layout.users.passwordpanel:PersonalPreferencesPanel",
)
zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.passwordpanel import PersonalPreferencesConfiglet instead.",
    PersonalPreferencesConfiglet="plone.app.layout.users.passwordpanel:PersonalPreferencesConfiglet",
)


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
