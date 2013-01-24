from zope.component import getUtility
from zope.interface import Interface, implements
from plone.schemaeditor.browser.schema.traversal import SchemaContext
from userdataschema import IUserDataSchemaProvider
from plone.supermodel.utils import syncSchema
from Products.CMFCore.utils import getToolByName


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
    pm = getToolByName(object, 'portal_memberdata')
    syncSchema(object.schema, pm.schema, overwrite=True)
    import pdb; pdb.set_trace( )
