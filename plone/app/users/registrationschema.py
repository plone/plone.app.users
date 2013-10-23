from Products.CMFPlone import PloneMessageFactory as _
from zope import schema
from zope.interface import Interface


class IRegistrationSchema(Interface):

    user_registration_fields = schema.Tuple(
        title=_(
            u'title_user_registration_fields',
            default=u'User registration fields'
        ),
        description=_(
            u"description_user_registration_fields",
            default=(u"Select the fields for the join form. Fields in the "
                     u"right box will be shown on the form, fields on the "
                     u"left are disabled. Use the left/right buttons to move "
                     u"a field from right to left (to disable it) and vice "
                     u"versa. Use the up/down buttons to change the order in "
                     u"which the fields appear on the form."),
        ),
        value_type=schema.Choice(
            vocabulary='plone.app.users.user_registration_fields'),
    )
