from zope.component import getMultiAdapter
from z3c.form import form, field, button
from z3c.form.browser.orderedselect import OrderedSelectFieldWidget

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from plone.protect import CheckAuthenticator

from ..registration import USER_REGISTRATION_FIELDS
from ..registrationschema import IZ3CRegistrationSchema


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
        # CSRF protection
        CheckAuthenticator(self.request)

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
