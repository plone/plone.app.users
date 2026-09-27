import zope.deferredimport

zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.membersearch import IMemberSearchSchema instead.",
    IMemberSearchSchema="plone.app.layout.users.membersearch:IMemberSearchSchema",
)
zope.deferredimport.deprecated(
    "Please use from plone.app.layout.users.membersearch import MemberSearchForm instead.",
    MemberSearchForm="plone.app.layout.users.membersearch:MemberSearchForm",
)
