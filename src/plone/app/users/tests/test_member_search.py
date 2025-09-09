from plone.app.users.browser.membersearch import extractCriteriaFromRequest

import unittest


class TestMemberSearch(unittest.TestCase):
    def test_extract_criteria_from_request(self):
        data = {
            "_authenticator": "ab4731...",
            "form.buttons.search": "Search",
            "form.widgets.something": "any form value",
            "form.widgets.roles-empty-marker": True,
        }

        result = extractCriteriaFromRequest(data)

        self.assertEqual(result, {"something": "any form value"})
