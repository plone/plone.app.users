from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.app.users.browser.account import getSchema
from plone.app.users.schema import ICombinedRegisterSchema
from zope.deferredimport import deprecated

deprecated(
    "Import from plone.app.users.utils instead.",
    RENAME_AFTER_CREATION_ATTEMPTS="plone.app.users.utils:RENAME_AFTER_CREATION_ATTEMPTS",
)

deprecated(
    "Please use from plone.app.layout.users.register import BaseRegistrationForm instead.",
    BaseRegistrationForm="plone.app.layout.users.register:BaseRegistrationForm",
)
deprecated(
    "Please use from plone.app.layout.users.register import RegistrationForm instead.",
    RegistrationForm="plone.app.layout.users.register:RegistrationForm",
)
deprecated(
    "Please use from plone.app.layout.users.register import AddUserForm instead.",
    AddUserForm="plone.app.layout.users.register:AddUserForm",
)


def getRegisterSchema():
    schema = getSchema(
        ICombinedRegisterSchema,
        AccountPanelSchemaAdapter,
        form_name="On Registration",
    )
    return schema
