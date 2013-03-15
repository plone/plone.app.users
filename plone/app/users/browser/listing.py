from zope.component import queryUtility, getUtility
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
from plone.schemaeditor.browser.field import order
from plone.protect import CheckAuthenticator
from ZTUtils import make_query

from ..userdataschema import IUserDataSchemaProvider

class NotEditableField(Exception):pass


class SchemaListing(listing.SchemaListing):
    template = ViewPageTemplateFile('schema_listing.pt')

    @button.buttonAndHandler(_(u'Save Defaults'))
    def handleSaveDefaults(self, action):
        CheckAuthenticator(self.request)
        listing.SchemaListing.handleSaveDefaults(self, action)

    def render(self):
        # for widget in self._iterateOverWidgets():
        #     # disable fields from behaviors
        #     if widget.field.__name__ not in fields:
        #         widget.disabled = 'disabled'
        return super(listing.SchemaListing, self).render()

    def field_classes(self, field):
        classes = ['fieldPreview', 'orderable']
        return ' '.join(classes)

    def edit_url(self, field):
        return super(SchemaListing, self).edit_url(field)

    def delete_url(self, field):
        baseSchema = getUtility(IUserDataSchemaProvider).baseSchema
        if not field.__name__ in [a for a in baseSchema]:
            return '%s/%s/@@memberfield_delete' % (
                self.context.absolute_url(), field.__name__)

class ReadOnlySchemaListing(SchemaListing):pass

class SchemaListingPage(listing.SchemaListingPage):
    """
    """
    form = SchemaListing
    index = ViewPageTemplateFile('schema_layout.pt')

    def makeQuery(self, **kw):
        return make_query(**kw)

class FieldOrderView(order.FieldOrderView):
    def checkEditableField(self):
        baseSchema = getUtility(IUserDataSchemaProvider).baseSchema
        if self.field.__name__ in [a for a in baseSchema]:
            raise NotEditableField("Default field, not editable")

    def move(self, pos):
        super(FieldOrderView, self).move(pos)

    def delete(self):
        self.checkEditableField()
        super(FieldOrderView, self).delete()

