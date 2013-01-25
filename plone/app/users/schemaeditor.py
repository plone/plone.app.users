from zope.component import getUtility
from zope.component.hooks import getSite
from zope.annotation.interfaces import IAnnotations
from zope.interface import Interface, implements

from plone.schemaeditor.browser.schema.traversal import SchemaContext

from userdataschema import IUserDataSchemaProvider, SCHEMA_ANNOTATION


class IMemberSchemaContext(Interface):
    """
    """


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
