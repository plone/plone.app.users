import copy
from zope.interface import implements
from zope.interface import Interface
from zope.component import provideAdapter
from plone.memoize import volatile
from plone.supermodel.model import finalizeSchemas, SchemaClass
from plone.app.layout.navigation.interfaces import INavigationRoot

from .userdatapanel import UserDataPanelAdapter
from .account import AccountPanelSchemaAdapter

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

    def getSchema(self):
        schema = super(UserDataSchemaProvider, self).getSchema()
        # make forms adapters know about ttw fields
        # we force self.schema as it can be a
        # generated supermodel with TTw fields
        provideAdapter(UserDataPanelAdapter, (Interface,), schema)
        # as schema is a generated supermodel, just insert a relevant
        # adapter for it
        # provideAdapter(
        #    factory=UserDataPanelAdapter,
        #    adapts=(INavigationRoot,),
        #    provides=schema
        # )
        return schema


class RegisterSchemaProvider(BaseMemberSchemaProvider):
    implements(IRegisterSchemaProvider)
    baseSchema = ICombinedRegisterSchema

    def getSchema(self):
        schema = super(RegisterSchemaProvider, self).getSchema()
        provideAdapter(RegisterSchemaProvider, (INavigationRoot,), schema)
        return schema
