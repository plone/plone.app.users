from zope.component import getUtility, provideAdapter, adapter, adapts
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, implements
from zope import schema
from zope.schema.interfaces import IField

from plone.schemaeditor.browser.schema.traversal import SchemaContext
from plone.schemaeditor.interfaces import IFieldEditorExtender
from Products.CMFPlone import PloneMessageFactory as _

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
        in_registration = self.field.interface.queryTaggedValue('in_registration', {})
        return in_registration.get(self.field.__name__)

    def _set_in_registration(self, value):
        in_registration = self.field.interface.queryTaggedValue('in_registration', {})
        in_registration[self.field.__name__] = value
        self.field.interface.setTaggedValue('in_registration', in_registration)

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
    annotations[SCHEMA_ANNOTATION] = object.schema._InterfaceClass__attrs
