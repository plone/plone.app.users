import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.passwordpanel import IPasswordSchema instead.",
    IPasswordSchema="plone.app.layout.users.passwordpanel:IPasswordSchema",
)
zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.passwordpanel import PasswordPanel instead.",
    PasswordPanel="plone.app.layout.users.passwordpanel:PasswordPanel",
)
zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.passwordpanel import PasswordPanelAdapter instead.",
    PasswordPanelAdapter="plone.app.layout.users.passwordpanel:PasswordPanelAdapter",
)
