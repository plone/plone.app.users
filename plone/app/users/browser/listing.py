from zope.component import queryUtility
from zope.event import notify
from zope.interface import implements
from z3c.form import button, form
from z3c.form.interfaces import IEditForm, DISPLAY_MODE

from plone.z3cform.layout import FormWrapper
from plone.memoize.instance import memoize
from plone.autoform.form import AutoExtensibleForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.schemaeditor import SchemaEditorMessageFactory as _
from plone.schemaeditor.interfaces import IFieldFactory
from plone.schemaeditor.utils import SchemaModifiedEvent

from plone.schemaeditor.browser.schema import listing
from plone.protect import CheckAuthenticator
from ZTUtils import make_query

class SchemaListing(listing.SchemaListing):
    template = ViewPageTemplateFile('schema_listing.pt')
 
    @button.buttonAndHandler(_(u'Save Defaults'))
    def handleSaveDefaults(self, action):
        CheckAuthenticator(self.request)
        listing.SchemaListing.handleSaveDefaults(self, action)

class ReadOnlySchemaListing(SchemaListing):pass

class SchemaListingPage(listing.SchemaListingPage):
    """
    """
    form = SchemaListing
    index = ViewPageTemplateFile('schema_layout.pt')

    def makeQuery(self, **kw):
        return make_query(**kw)
