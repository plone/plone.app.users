# Note: test setup somehow fails when only tests from this file are run.
from zope.component import getSiteManager
from zope.component import getMultiAdapter

from plone.app.users.browser.membersearch import extractCriteriaFromRequest
from plone.app.users.tests.base import BaseTestCase
from plone.app.users.utils import uuid_userid_generator


class TestMemberSearch(BaseTestCase):

    def test_extract_criteria_from_request(self):
        data = {
            '_authenticator': u'ab4731...',
            'form.buttons.search': u'Search',
            'form.widgets.something': u'any form value',
            'form.widgets.roles-empty-marker': True,
        }
        result = extractCriteriaFromRequest(data)

        self.assertEqual(result, {"something": u'any form value'})

    # TODO: write the test
    def test_view_member_search(self):
        """ Test that member search view is registered for Folders.
        """
        pass
