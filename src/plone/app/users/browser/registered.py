import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.register import RegisteredView instead.",
    RegisteredView="plone.app.layout.users.register:RegisteredView",
)
