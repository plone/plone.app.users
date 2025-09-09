from importlib.resources import files
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.users.tests.base import BaseTestCase


class TestPortrait(BaseTestCase):
    def test_regression_supported_image_type_122(self):
        # https://github.com/plone/plone.app.users/issues/122

        self.browser.open("http://nohost/plone/")
        self.browser.getLink("Log in").click()
        self.browser.getControl("Login Name").value = SITE_OWNER_NAME
        self.browser.getControl("Password").value = SITE_OWNER_PASSWORD
        self.browser.getControl("Log in").click()
        self.browser.open("http://nohost/plone/@@personal-information")
        self.browser.getControl(name="form.widgets.email").value = "test@test.com"
        path = files("plone.app.users").joinpath("tests/onepixel.jpg")
        with open(path, "rb") as file_handle:
            portrait_file = file_handle.read()
        self.browser.getControl(name="form.widgets.portrait").add_file(
            portrait_file, "image/jpg", "onepixel.# jpg"
        )
        self.browser.getControl("Save").click()
        self.assertIn("Changes saved.", self.browser.contents)

    def test_not_supported_image_type_122(self):
        # https://github.com/plone/plone.app.users/issues/122

        self.browser.open("http://nohost/plone/")
        self.browser.getLink("Log in").click()
        self.browser.getControl("Login Name").value = SITE_OWNER_NAME
        self.browser.getControl("Password").value = SITE_OWNER_PASSWORD
        self.browser.getControl("Log in").click()
        self.browser.open("http://nohost/plone/@@personal-information")
        self.browser.getControl(name="form.widgets.email").value = "test@test.com"
        path = files("plone.app.users").joinpath("tests/transparent_square.svg")
        with open(path, "rb") as file_handle:
            portrait_file = file_handle.read()
        self.browser.getControl(name="form.widgets.portrait").add_file(
            portrait_file, "image/svg+xml", "onepixel.# jpg"
        )
        self.browser.getControl("Save").click()
        self.assertIn(
            "The file you selected is not supported by Pillow. Please choose another.",
            self.browser.contents,
        )
