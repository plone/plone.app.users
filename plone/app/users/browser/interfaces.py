# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces.controlpanel import IPloneControlPanelForm
from zope.interface import Interface


class IAccountPanelForm(IPloneControlPanelForm):
    """Forms using plone.app.users
    """

    def _on_save():
        """Callback mehod which can be implemented by control panels to
        react when the form is successfully saved. This avoids the need
        to re-define actions only to do some additional notification or
        configuration which cannot be handled by the normal schema adapter.

        By default, does nothing.
        """


class IUserIdGenerator(Interface):
    """Create a user id from data.

    This must be a function that accepts 'data' as an argument.
    'data' is a dictionary.  Normally it will contain keys like
    username, email, fullname, password that the user has filled in on
    the registration form.  Nothing is guaranteed though, so you
    should not assume that a key is present.

    Standard behavior would be to use the username (login name) as
    user id.  When Plone is configured to use the email address as
    login name, no username will be in the data, because the form
    will not contain that field.  Standard behavior was to use the
    email address as user id as well.  That has some downsides, as
    explained in the generate_user_id method of the registration
    view, so this was changed to create a user id based on the
    full name.

    By registering a utility for this interface, you can come up
    with a different scheme, for example to create a uuid.  Plone
    does not have such a utility, but you can look in the tests
    for an example.

    The function should return the chosen user id or None.
    """


class ILoginNameGenerator(Interface):
    """Create a login name from data.

    This must be a function that accepts 'data' as an argument.
    'data' is a dictionary.  Normally it will contain keys like
    username, email, fullname, password that the user has filled in on
    the registration form.  Nothing is guaranteed though, so you
    should not assume that a key is present.

    Standard behavior is to use the username as login name.  When
    Plone is configured to use the email address as login name, we
    take the email key.

    By registering a utility for this interface, you can come up
    with a different scheme, for example to create a uuid.  Plone
    does not have such a utility, but you can look in the tests
    for an example.

    The function should return the chosen login name or None.
    """
