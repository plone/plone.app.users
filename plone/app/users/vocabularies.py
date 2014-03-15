from AccessControl import getSecurityManager

from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema import getFieldNames
from zope.component import getUtility
from zope.site.hooks import getSite

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal
from Products.CMFPlone.utils import normalizeString, safe_unicode

from .schemaeditor import get_validators
from .userdataschema import IUserDataSchemaProvider
from plone.app.users.browser.register import RegistrationForm


# Define constants from the Join schema that should be added to the
# vocab of the join fields setting in usergroupssettings controlpanel.
JOIN_CONST = ['username', 'password', 'email', 'mail_me']


class UserRegistrationFieldsVocabulary(object):
    """Returns list of fields available for registration form.

    It gets fields from UserDataSchemaProvider (which includes
    TTW defined fields).

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
      ['description', 'home_page', 'location', 'portrait', 'fullname', 'email', 'username', 'password', 'mail_me']

      >>> email = fields.by_token['email']
      >>> email.title, email.token, email.value
      ('email', 'email', 'email')

    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        # complete list of user data form fields
        util = getUtility(IUserDataSchemaProvider)
        schema = util.getSchema()
        values = getFieldNames(schema)

        # make sure required minimum number of fields is present
        for val in JOIN_CONST:
            if val not in values:
                values.append(val)

        return SimpleVocabulary([SimpleTerm(v, v, v) for v in values])

UserRegistrationFieldsVocabularyFactory = UserRegistrationFieldsVocabulary()


class AdaptersVocabulary(object):
    """MemberField validators vocabulary"""
    implements(IVocabularyFactory)
    def __call__(self, context, key=None):
        funcs = get_validators()
        validators = dict([(a, funcs[a]['doc'])
                           for a in funcs])
        terms = [SimpleTerm(baseNormalize(validator),
                            baseNormalize(validator),
                            validators[validator])
                 for validator in validators]
        return SimpleVocabulary(terms)

AdaptersVocabularyFactory = AdaptersVocabulary()


class GroupIdVocabulary(object):
    """
    Return vocab of groups to add new user to.

      >>> from zope.component import queryUtility
      >>> from zope.schema.interfaces import IVocabularyFactory
      >>> from Products.CMFCore.utils import getToolByName

      >>> groups_tool = getToolByName(self.portal, 'portal_groups')
      >>> groups_tool.addGroup(
      ...     'fancygroup', [], [],
      ...     title='Group Title',
      ...     description="Group Description",
      ... )
      True

      >>> name = 'plone.app.users.group_ids'
      >>> util = queryUtility(IVocabularyFactory, name)

      >>> fields = util(self.portal)
      >>> fields
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> [k.value for k in fields] # doctest: +NORMALIZE_WHITESPACE
      ['fancygroup', 'Reviewers', 'Site Administrators']
      >>> [k.title for k in fields] # doctest: +NORMALIZE_WHITESPACE
      [u'Group Title (fancygroup)', u'Reviewers', u'Site Administrators']

    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        groups_tool = getToolByName(site, 'portal_groups')
        is_zope_manager = getSecurityManager().checkPermission(
            ManagePortal, context)
        groups = groups_tool.listGroups()

        # Get group id, title tuples for each, omitting virtual group
        # 'AuthenticatedUsers'
        terms = []
        for g in groups:
            if g.id == 'AuthenticatedUsers':
                continue
            if 'Manager' in g.getRoles() and not is_zope_manager:
                continue

            group_title = safe_unicode(g.getGroupTitleOrName())
            if group_title != g.id:
                title = u'%s (%s)' % (group_title, g.id)
            else:
                title = group_title
            terms.append(SimpleTerm(g.id, g.id, title))

        # Sort by title
        terms.sort(key=lambda x: normalizeString(x.title))
        return SimpleVocabulary(terms)


GroupIdVocabularyFactory = GroupIdVocabulary()
