Testing the member search form
==============================

This is about the 'member_search' form. This test will try to use the form as
anonymous. Then login as a Plone user, and try again.

    >>> view_name = '@@member-search'
    >>> browser = self.browser

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

So let's login as Plone user and try again:

    >>> browser.getLink('Log in').click()
    >>> browser.getControl('Login Name').value = 'test_user_1_'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()

Now we should be on the member search as a logged in user:

    >>> 'Login Name' in browser.contents
    False
    >>> browser.url.endswith(view_name)
    True

So let's search again. We should see two Members (admin, test_user_1_):

    >>> browser.getControl(name='form.buttons.search').click()
    >>> '2 items matching your search terms.' in browser.contents
    True
    >>> '<a href="http://nohost/plone/Members/test_user_1_">'in browser.contents
    True
    >>> '<a href="http://nohost/plone/author/admin">'in browser.contents
    True
