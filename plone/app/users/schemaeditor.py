from zope.component import getUtility, provideAdapter, adapter, adapts
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, implements
from zope import schema
from zope.schema.interfaces import IField

from plone.schemaeditor.browser.schema.traversal import SchemaContext
from plone.schemaeditor.interfaces import IFieldEditorExtender
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

from userdataschema import IUserDataSchemaProvider, SCHEMA_ANNOTATION


class IMemberField(Interface):

    in_registration = schema.Bool(
        title=_(
            u'label_also_in_registration',
            default=u'Display in registration form'),
        description=u'',
        required=False)


class IMemberSchemaContext(Interface):
    """
    """


@adapter(IMemberSchemaContext, IField)
def get_member_field_schema(schema_context, field):
    return IMemberField

provideAdapter(
    get_member_field_schema,
    provides=IFieldEditorExtender,
    name='plone.app.users.memberfield')


class MemberFieldAdapter(object):
    adapts(IField)

    def __init__(self, field):
        self.field = field

    def _get_in_registration(self):
        in_registration = self.field.queryTaggedValue('in_registration', False)
        return in_registration

    def _set_in_registration(self, value):
        self.field.setTaggedValue('in_registration', value)

    in_registration = property(_get_in_registration, _set_in_registration)

provideAdapter(MemberFieldAdapter, provides=IMemberField)


class MemberSchemaContext(SchemaContext):
    implements(IMemberSchemaContext)

    def __init__(self, context, request):
        schema = getUtility(IUserDataSchemaProvider).getSchema()
        super(MemberSchemaContext, self).__init__(
            schema,
            request,
            name='member-fields'
        )


def updateSchema(object, event):
    site = getSite()
    annotations = IAnnotations(site)
    old_schema = annotations.get(SCHEMA_ANNOTATION, {})
    new_schema = object.schema._InterfaceClass__attrs

    # store the extra schema in an annotation
    annotations[SCHEMA_ANNOTATION] = new_schema

    # update portal_memberdata properties
    pm = getToolByName(site, "portal_memberdata")
    field_type_mapping = {
        "TextLine": 'text',
        "Text": 'lines',
        "Int": 'int',
        "Float": 'float',
        "Bool": 'boolean',
        "Datetime": 'date',
        "Date": 'date',
        "Choice": 'text',
        "List": 'text',
    }

    existing = pm.propertyIds()
    for field_id in new_schema.keys():
        field_type = field_type_mapping.get(
            new_schema[field_id].__class__.__name__,
            None)
        if not field_type:
            continue
        if field_id in existing:
            pm._delProperty(field_id)
        pm._setProperty(field_id, '', field_type)

    to_remove = [field_id for field_id in old_schema.keys()
                    if field_id not in new_schema.keys()]
    for field_id in to_remove:
        pm._delProperty(field_id)
