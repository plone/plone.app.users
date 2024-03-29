from .browser.schemaeditor import getFromBaseSchema
from AccessControl import getSecurityManager
from plone.app.users.schema import ICombinedRegisterSchema
from plone.base.utils import safe_text
from plone.i18n.normalizer.interfaces import IIDNormalizer
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import get_portal
from zope.component import queryUtility
from zope.interface import implementer
from zope.schema import getFieldNames
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


# Define constants from the Join schema that should be added to the
# vocab of the join fields setting in usergroupssettings controlpanel.
JOIN_CONST = ["username", "password", "email", "mail_me"]


@implementer(IVocabularyFactory)
class UserRegistrationFieldsVocabulary:
    """Returns list of fields available for registration form.

    It gets fields from z3c.form adopted Registration form schema.
    FormExtender fields are not included.

      >>> from zope.component import queryUtility
      >>> from zope.schema.interfaces import IVocabularyFactory

      >>> name = 'plone.app.users.user_registration_fields'
      >>> util = queryUtility(IVocabularyFactory, name)

      >>> fields = util(None)
      >>> fields
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(fields.by_token)
      10
      >>> values = [k.value for k in fields]
      >>> sorted(values)
      ['description', 'email', 'fullname', 'home_page', 'location', 'mail_me', 'password', 'password_ctl', 'portrait', 'username']

      >>> email = fields.by_token['email']
      >>> email.title, email.token, email.value
      ('email', 'email', 'email')

    """

    def __call__(self, context):
        # default list of Registration Form fields
        schema = getFromBaseSchema(ICombinedRegisterSchema)
        values = getFieldNames(schema)

        # make sure required minimum number of fields is present
        for val in JOIN_CONST:
            if val not in values:
                values.append(val)

        return SimpleVocabulary([SimpleTerm(v, v, v) for v in values])


UserRegistrationFieldsVocabularyFactory = UserRegistrationFieldsVocabulary()


@implementer(IVocabularyFactory)
class GroupIdVocabulary:
    """
    Return vocab of groups to add new user to.

      >>> from zope.component import queryUtility
      >>> from zope.schema.interfaces import IVocabularyFactory
      >>> from Products.CMFPlone.utils import get_portal
      >>> from Products.CMFCore.utils import getToolByName

      >>> groups_tool = getToolByName(get_portal(), 'portal_groups')
      >>> groups_tool.addGroup(
      ...     'fancygroup', [], [],
      ...     title='Group Title',
      ...     description="Group Description",
      ... )
      True

      >>> name = 'plone.app.users.group_ids'
      >>> util = queryUtility(IVocabularyFactory, name)

      >>> fields = util(get_portal())
      >>> fields
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> [k.value for k in fields] # doctest: +NORMALIZE_WHITESPACE
      ['fancygroup', 'Reviewers', 'Site Administrators']
      >>> [k.title for k in fields] # doctest: +NORMALIZE_WHITESPACE
      ['Group Title (fancygroup)', 'Reviewers', 'Site Administrators']

    """

    def __call__(self, context):
        site = get_portal()
        groups_tool = getToolByName(site, "portal_groups")
        is_zope_manager = getSecurityManager().checkPermission(ManagePortal, context)
        groups = groups_tool.listGroups()

        # Get group id, title tuples for each, omitting virtual group
        # 'AuthenticatedUsers'
        terms = []
        for g in groups:
            if g.id == "AuthenticatedUsers":
                continue
            if "Manager" in g.getRoles() and not is_zope_manager:
                continue

            group_title = safe_text(g.getGroupTitleOrName())
            if group_title != g.id:
                title = f"{group_title} ({g.id})"
            else:
                title = group_title
            terms.append(SimpleTerm(g.id, g.id, title))

        # Sort by title
        utility = queryUtility(IIDNormalizer)
        terms.sort(key=lambda x: utility.normalize(x.title))
        return SimpleVocabulary(terms)


GroupIdVocabularyFactory = GroupIdVocabulary()
