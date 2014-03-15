import unittest


class TestMemberSearch(unittest.TestCase):

    def test_extract_criteria_from_request(self):
        data = {
            '_authenticator': u'ab4731...',
            'form.buttons.search': u'Search',
            'form.widgets.something': u'any form value',
            'form.widgets.roles-empty-marker': True,
        }

        from plone.app.users.browser.membersearch import extractCriteriaFromRequest
        result = extractCriteriaFromRequest(data)

        self.assertEqual(result, {"something": u'any form value'})
