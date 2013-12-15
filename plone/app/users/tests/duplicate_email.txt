Test duplicate mail addresses
=============================

When email address is used as login name, duplicates are not allowed.

Use email addresses as login name:

    >>> ptool = self.portal.portal_properties
    >>> ptool.site_properties._updateProperty('use_email_as_login', True)

Create a new user one:

    >>> mtool = self.portal.portal_membership
    >>> mtool.addMember('userone@example.com', 'secret', [], [])
    >>> userone = mtool.getMemberById('userone@example.com')
    >>> userone.setMemberProperties({'email':'userone@example.com'})

Create a new user two:

    >>> mtool.addMember('usertwo@example.com', 'secret', [], [])
    >>> usertwo = mtool.getMemberById('usertwo@example.com')
    >>> usertwo.setMemberProperties({'email':'usertwo@example.com'})

Login as user two:

    >>> self.browser.open('http://nohost/plone/')
    >>> self.browser.getLink('Log in').click()

    >>> self.browser.getControl('E-mail').value = 'usertwo@example.com'
    >>> self.browser.getControl('Password').value = 'secret'
    >>> self.browser.getControl('Log in').click()
    >>> 'Login failed' in self.browser.contents
    False

Now we should be able to access the user data panel:

    >>> self.browser.open('http://nohost/plone/@@personal-information')
    >>> 'Login Name' in self.browser.contents
    False
    >>> self.browser.url.endswith('@@personal-information')
    True

Setting the e-mail address to an existing one should give an error message:

    >>> self.browser.getControl('E-mail').value = 'userone@example.com'
    >>> self.browser.getControl('Save').click()
    >>> 'The email address you selected is already in use' in self.browser.contents
    True
    >>> 'Changes saved' in self.browser.contents
    False
