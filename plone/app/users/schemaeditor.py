from Acquisition import aq_inner
from zope.component import getUtility
from plone.schemaeditor.browser.schema.listing import SchemaListing
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from Products.CMFPlone import PloneMessageFactory as _
from userdataschema import IUserDataSchemaProvider
from plone.z3cform.layout import FormWrapper


class SchemaEditorPage(FormWrapper):
    label = _(u'Fields')

    def __init__(self, context, request):
        self.request = request
        schema = getUtility(IUserDataSchemaProvider).getSchema()
        self.context = SchemaContext(schema, request, name='@@member-fields')
        #import pdb; pdb.set_trace( )

        if self.form is not None:
            self.form_instance = self.form(
                aq_inner(self.context), self.request)
            self.form_instance.__name__ = self.__name__

    @property
    def form(self):
        return SchemaListing
