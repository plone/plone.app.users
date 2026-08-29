import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.account import IMemberSearchSchema instead.",
    IMemberSearchSchema="plone.app.layout.users.account:IMemberSearchSchema",
)
zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.account import MemberSearchForm instead.",
    MemberSearchForm="plone.app.layout.users.account:MemberSearchForm",
)
