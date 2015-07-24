import copy
from zope.interface import implements
from zope.component import provideAdapter
from plone.supermodel.model import finalizeSchemas, SchemaClass
from Products.CMFPlone.interfaces import IPloneSiteRoot

from .userdatapanel import UserDataPanelAdapter
from .account import AccountPanelSchemaAdapter
from .schemaeditor import copy_schema

from .schemaeditor import SCHEMATA_KEY, get_ttw_edited_schema
from plone.app.users.schema import (
    IUserDataSchema,
    ICombinedRegisterSchema,
    IUserDataSchemaProvider,
    IRegisterSchemaProvider)


class BaseMemberSchemaProvider(object):
    """Base mixin class for members schema providers
    """

    def __init__(self):
        self._schema = None

    def getSchema(self):
        if not self._schema:
            self.initialize()
        return self._schema

    def loadSchema(self):
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

    def initialize(self):
        self._schema = self.loadSchema()
        # as schema is a generated supermodel,
        # needed adapters can only be registered at run time
        provideAdapter(UserDataPanelAdapter, (IPloneSiteRoot,), self._schema)

    def getCopyOfSchema(self):
        schema = self.getSchema()
        copy = copy_schema(schema, filter_serializable=True)
        # as schema is a generated supermodel,
        # needed adapters can only be registered at run time
        provideAdapter(UserDataPanelAdapter, (IPloneSiteRoot,), copy)
        return copy


class RegisterSchemaProvider(BaseMemberSchemaProvider):
    implements(IRegisterSchemaProvider)
    baseSchema = ICombinedRegisterSchema

    def initialize(self):
        self._schema = self.loadSchema()
        # as schema is a generated supermodel,
        # needed adapters can only be registered at run time
        provideAdapter(
            AccountPanelSchemaAdapter, (IPloneSiteRoot,), self._schema)
