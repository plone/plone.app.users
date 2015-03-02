Test duplicate mail addresses
=============================

When email address is used as login name, duplicates are not allowed.

Use email addresses as login name:

    >>> from plone.app.users.tests.base import get_security_settings
    >>> security_settings = get_security_settings()
    >>> security_settings.use_email_as_login = True

Create a new user one:

    >>> portal = layer['portal']
    >>> mtool = portal.portal_membership
    >>> mtool.addMember('userone@example.com', 'secret', [], [])
    >>> userone = mtool.getMemberById('userone@example.com')
    >>> userone.setMemberProperties({'email':'userone@example.com'})

Create a new user two:

    >>> mtool.addMember('usertwo@example.com', 'secret', [], [])
    >>> usertwo = mtool.getMemberById('usertwo@example.com')
    >>> usertwo.setMemberProperties({'email':'usertwo@example.com'})
    >>> from transaction import commit
    >>> commit()

Login as user two:

    >>> from plone.testing.z2 import Browser
    >>> browser = Browser(layer['app'])
    >>> browser.open('http://nohost/plone/')
    >>> browser.getLink('Log in').click()

    >>> browser.getControl('E-mail').value = 'usertwo@example.com'
    >>> browser.getControl('Password').value = 'secret'
    >>> browser.getControl('Log in').click()
    >>> 'Login failed' in browser.contents
    False

Now we should be able to access the user data panel:

    >>> browser.open('http://nohost/plone/@@personal-information')
    >>> 'Login Name' in browser.contents
    False
    >>> browser.url.endswith('@@personal-information')
    True

Setting the e-mail address to an existing one should give an error message:

    >>> browser.getControl('E-mail').value = 'userone@example.com'
    >>> browser.getControl('Save').click()
    >>> 'The email address you selected is already in use' in browser.contents
    True
    >>> 'Changes saved' in browser.contents
    False
