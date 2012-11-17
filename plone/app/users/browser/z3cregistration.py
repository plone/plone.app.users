from zope import schema
from zope.interface import Interface, implementsOnly
from zope.component import getMultiAdapter
from z3c.form import form, field, button
from z3c.form.interfaces import IWidgets
from z3c.form.browser.orderedselect import OrderedSelectFieldWidget

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from ..registration import USER_REGISTRATION_FIELDS


class EmptyPrefixFieldWidgets(field.FieldWidgets):
    """Override default Field Widgets to get rid of prefix"""
    implementsOnly(IWidgets)
    prefix = ''

class IZ3CRegistrationSchema(Interface):

    user_registration_fields = schema.Tuple(
        title=_(u'title_user_registration_fields',
                 default=u'User registration fields'),
        description=_(u"description_user_registration_fields",
            default=(u"Select the fields for the join form. Fields in the "
            u"right box will be shown on the form, fields on the left are "
            u"disabled. Use the left/right buttons to move a field from right "
            u"to left (to disable it) and vice versa. Use the up/down buttons "
            u"to change the order in which the fields appear on the form."),
        ),
        value_type=schema.Choice(
            vocabulary='plone.app.users.user_registration_fields'),
    )

class RegistrationControlPanel(form.Form):

    label = _(u"Registration settings")
    description = _(u"Registration settings for this site.")
    form_name = _(u"Registration settings")
    
    formErrorsMessage = _('There were errors.')
    template = ViewPageTemplateFile('z3c-memberregistration.pt')

    fields = field.Fields(IZ3CRegistrationSchema)
    fields['user_registration_fields'].widgetFactory = OrderedSelectFieldWidget

    def getContent(self):
        props = self.props()
        return {'user_registration_fields': props.getProperty(
            USER_REGISTRATION_FIELDS, [])}

    @button.buttonAndHandler(_(u'label_save', default=u'Save'), name='save')
    def action_save(self, action):
        data, errors = self.extractData()
        if errors:
            IStatusMessage(self.request).addStatusMessage(
                self.formErrorsMessage, type='error')
            return
        
        # save property
        if data['user_registration_fields'] != \
            self.getContent()['user_registration_fields']:
            props = self.props()
            props._updateProperty(USER_REGISTRATION_FIELDS,
                data['user_registration_fields'])
            msg = _("Changes saved.")
        else:
            msg = _("No changes made.")
        IStatusMessage(self.request).addStatusMessage(msg, type="info")

    @button.buttonAndHandler(_(u'label_cancel', default=u'Cancel'),
        name='cancel')
    def action_cancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_("Changes canceled."),
            type="info")
        url = getMultiAdapter((self.context, self.request),
            name='absolute_url')()
        self.request.response.redirect(url + '/plone_control_panel')

    def props(self):
        pprop = getToolByName(self.context, 'portal_properties')
        return pprop.site_properties
