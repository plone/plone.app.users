==============================
Testing the member search form
==============================

This is about the 'member_search' form. This test will try to use the form as
anonymous. Then login as a Plone user, and try again.

Set up
======

    >>> from plone.app.testing import SITE_OWNER_NAME
    >>> from plone.app.testing import SITE_OWNER_PASSWORD
    >>> from plone.app.testing import TEST_USER_NAME
    >>> from plone.app.testing import TEST_USER_PASSWORD
    >>> from plone.testing.z2 import Browser

    >>> app = layer['app']
    >>> portal = layer['portal']

    >>> view_name = '@@member-search'

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

Manager creates a user
----------------------

Login as manager:

    >>> browser.open('http://nohost/plone/login_form')
    >>> browser.getControl('Login Name').value = SITE_OWNER_NAME
    >>> browser.getControl('Password').value = SITE_OWNER_PASSWORD
    >>> browser.getControl('Log in').click()

Go to the add new user form:

    >>> browser.open('http://nohost/plone/@@usergroup-userprefs')
    >>> browser.getLink('Add New User').click()

Fill out the form.

    >>> browser.getControl('Full Name').value = 'Bob Jones'
    >>> browser.getControl('User Name').value = 'bob-jones'
    >>> browser.getControl('E-mail').value = 'bob-jones+test2@example.com'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Confirm password').value = 'secret'
    >>> browser.getControl('Register').click()
    >>> browser.contents
    '...User added...bob-jones...'

Logout:

    >>> browser.getLink(url='http://nohost/plone/logout').click()
    >>> 'Log in' in browser.contents
    True

Member search as anonymous
==========================

Viewing this form should be possible for anonymous users:

    >>> browser.open('http://nohost/plone/' + view_name)
    >>> 'Search for users' in browser.contents
    True

We have these controls in the form:

    >>> browser.getControl(name='form.widgets.login').value
    ''
    >>> browser.getControl('E-mail').value
    ''
    >>> browser.getControl('Full Name').value
    ''

But they will not see any member of the portal.

    >>> browser.getControl(name='form.widgets.login').value = 'test_user_1_'
    >>> browser.getControl(name='form.buttons.search').click()
    >>> 'You are not allowed to list portal members.' in browser.contents
    True

Member search logged-in
=======================

So let's login as Plone user and try again:

    >>> browser.getLink('Log in').click()
    >>> browser.getControl('Login Name').value = TEST_USER_NAME
    >>> browser.getControl('Password').value = TEST_USER_PASSWORD
    >>> browser.getControl('Log in').click()

Now we should be on the member search as a logged in user:

    >>> 'Login Name' in browser.contents
    False
    >>> browser.url.endswith(view_name)
    True

So let's search again. We should see two members (test_user_1_ and bob):

    >>> browser.getControl(name='form.buttons.search').click()
    >>> '2 items matching your search terms.' in browser.contents
    True
    >>> '<a href="http://nohost/plone/Members/test_user_1_">'in browser.contents
    True
    >>> '<a href="http://nohost/plone/author/bob-jones">'in browser.contents
    True
