from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.site.hooks import getSite

from .browser.z3cpersonalpreferences import UserDataPanel
from .browser.register import JOIN_CONST


class UserRegistrationFieldsVocabulary(object):
    """Returns list of fields available for registration form.

    It gets fields from z3c.form adopted Personal Information form.
    IFormExtender fields will be included automatically if any.

      >>> from zope.component import queryUtility
      >>> from zope.schema.interfaces import IVocabularyFactory

      >>> name = 'plone.app.users.user_registration_fields'
      >>> util = queryUtility(IVocabularyFactory, name)

      >>> fields = util(None)
      >>> fields
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(fields.by_token)
      9
      >>> [k.value for k in fields]
      ['fullname', 'email', 'home_page', 'description', 'location', 'portrait', 'username', 'password', 'mail_me']

      >>> email = fields.by_token['email']
      >>> email.title, email.token, email.value
      ('email', 'email', 'email')

    Now register IFormExtender for UserDataPanel form and check if these extra
    fields are picked up by our vocabulary.

      >>> from zope import schema
      >>> from zope.interface import Interface
      >>> from zope.component import adapts, provideAdapter
      >>> from zope.publisher.interfaces.browser import IDefaultBrowserLayer
      >>> from plone.z3cform.fieldsets import extensible
      >>> from plone.app.users.browser.z3cpersonalpreferences import UserDataPanel

      >>> class IUserDataMusicSchema(Interface):
      ...     genre = schema.TextLine(title=u'Your favorite musical genre')
      ...     band = schema.TextLine(title=u'Your favorite musical band')

      >>> class UserDataPanelExtender(extensible.FormExtender):
      ...     adapts(Interface, IDefaultBrowserLayer, UserDataPanel)
      ...     def update(self):
      ...         self.add(IUserDataMusicSchema, index=1)
      ...         self.remove('home_page')

      >>> provideAdapter(factory=UserDataPanelExtender, name=u'musical-userdata')

    Now our vocubulary should return modified by form extender list of fields.

      >>> fields = util(None)
      >>> fields
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(fields.by_token)
      10
      >>> [k.value for k in fields]
      ['fullname', 'genre', 'band', 'email', 'description', 'location', 'portrait', 'username', 'password', 'mail_me']

      >>> genre = fields.by_token['genre']
      >>> genre.title, genre.token, genre.value
      ('genre', 'genre', 'genre')

    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        # prepare user data form fields, this is probably the only way to get
        # final list of available fields taking into account IFormExtender
        # adapters
        site = getSite()
        form = UserDataPanel(site, site.REQUEST)
        form.updateFields()
        values = [f for f in form.fields]
        
        # make sure required minimum number of fields is present
        for val in JOIN_CONST:
            if val not in values:
                values.append(val)

        return SimpleVocabulary([SimpleTerm(v, v, v) for v in values])

UserRegistrationFieldsVocabularyFactory = UserRegistrationFieldsVocabulary()
