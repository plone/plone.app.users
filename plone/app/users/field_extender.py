from zope.interface import Interface
from zope import schema

from zope.component import provideAdapter, adapter, adapts
from zope.schema.interfaces import IField
from plone.schemaeditor.interfaces import ISchemaContext

from .browser.schemaeditor import IMemberSchemaContext

from plone.schemaeditor.interfaces import IFieldEditorExtender

from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone.autoform import directives as form


from z3c.form.browser.checkbox import CheckBoxFieldWidget

form_vocab = SimpleVocabulary(
    [SimpleTerm(value=u'On Registration',
                title=u'On Registration'),
     SimpleTerm(value=u'User Profile View',
                title=u'User Profile View'),
     SimpleTerm(value=u'User Profile Edit',
                title=u'User Profile Edit'),]
)


class IUserFormSelection(Interface):
    form.widget(forms=CheckBoxFieldWidget)
    forms = schema.List(title=u"Where should this field be shown",
                        description=u"",
                        required=True,
                        value_type=schema.Choice(vocabulary=form_vocab),
                        )


@adapter(IMemberSchemaContext, IField)
def get_user_form_selection(schema_context, field):
    return IUserFormSelection

provideAdapter(get_user_form_selection, provides=IFieldEditorExtender, name='plone.app.users.userformselection')


class UserFormSelectionAdapter(object):
    adapts(IField)

    def __init__(self, field):
        self.field = field

    def _get_forms(self):
        forms = self.field.interface.queryTaggedValue('user_form_selection', {})
        return forms.get(self.field.__name__)
    def _set_forms(self, value):
        forms = self.field.interface.queryTaggedValue('user_form_selection', {})
        forms[self.field.__name__] = value
        self.field.interface.setTaggedValue('user_form_selection', forms)
    forms = property(_get_forms, _set_forms)

provideAdapter(UserFormSelectionAdapter, provides=IUserFormSelection)

