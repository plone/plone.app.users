import copy
from zope.interface import implements
from plone.memoize import volatile
from plone.supermodel.model import finalizeSchemas, SchemaClass

from .schemaeditor import (
    SCHEMATA_KEY,
    get_ttw_edited_schema,
    model_key,
    CACHE_CONTAINER)
from plone.app.users.schema import (
    IUserDataSchema,
    ICombinedRegisterSchema,
    IUserDataSchemaProvider,
    IRegisterSchemaProvider)


class BaseMemberSchemaProvider(object):
    """Base mixin class for members schema providers
    """

    @volatile.cache(lambda *args, **kw: "%s-%s" % (model_key(), args),
                    lambda *args: CACHE_CONTAINER)
    def getSchema(self):
        """
        """
        def copySchemaAttrs(schema):
            return dict([(a, copy.deepcopy(schema[a])) for a in schema])

        attrs = copySchemaAttrs(self.baseSchema)
        ttwschema = get_ttw_edited_schema()
        if ttwschema:
            attrs.update(copySchemaAttrs(ttwschema))
        schema = SchemaClass(SCHEMATA_KEY,
                             bases=(self.baseSchema,),
                             attrs=attrs)
        finalizeSchemas(schema)
        return schema


class UserDataSchemaProvider(BaseMemberSchemaProvider):
    implements(IUserDataSchemaProvider)
    baseSchema = IUserDataSchema


class RegisterSchemaProvider(BaseMemberSchemaProvider):
    implements(IRegisterSchemaProvider)
    baseSchema = ICombinedRegisterSchema
