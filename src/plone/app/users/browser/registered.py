import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.registered import RegisteredView instead.",
    RegisteredView="plone.app.layout.users.registered:RegisteredView",
)
