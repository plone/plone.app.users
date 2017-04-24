# -*- coding: utf-8 -*-
from plone.app.users.browser.schemaeditor import USERS_NAMESPACE
from plone.app.users.browser.schemaeditor import USERS_PREFIX
from plone.autoform import directives as form
from plone.supermodel.interfaces import IFieldMetadataHandler
from plone.supermodel.utils import ns
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope.component import adapts
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.interfaces import IField
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import zope.schema


form_vocab = SimpleVocabulary([
    SimpleTerm(value=u'On Registration',
               title=u'On Registration'),
    SimpleTerm(value=u'In User Profile',
               title=u'In User Profile'),
])


class IUserFormSelection(Interface):
    form.widget(forms=CheckBoxFieldWidget)
    forms = zope.schema.List(
        title=u"Where should this field be shown",
        description=u"Does not apply to username or to email fields",
        required=True,
        value_type=zope.schema.Choice(vocabulary=form_vocab),
    )


def get_user_form_selection(schema_context, field):
    return IUserFormSelection


def get_user_addform_selection(schema_context):
    return IUserFormSelection


class UserFormSelectionAdapter(object):
    adapts(IField)

    def __init__(self, field):
        self.field = field

    def _get_forms(self):
        forms = getattr(self.field, 'forms_selection', [])
        return forms

    def _set_forms(self, value):
        self.field.forms_selection = value

    forms = property(_get_forms, _set_forms)


@implementer(IFieldMetadataHandler)
class UserFormSelectionMetadata(object):

    namespace = USERS_NAMESPACE
    prefix = USERS_PREFIX

    def read(self, fieldNode, schema, field):
        forms = fieldNode.get(ns('forms', self.namespace))
        if forms:
            field.forms_selection = forms.split('|')

    def write(self, fieldNode, schema, field):
        forms = getattr(field, 'forms_selection', [])
        if forms:
            fieldNode.set(ns('forms', self.namespace), "|".join(forms))
