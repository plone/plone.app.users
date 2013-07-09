from zope.app.form.interfaces import IInputWidget
from zope.app.form.interfaces import ConversionError
from zope.component import adapts
from zope.i18nmessageid import MessageFactory
from zope.interface import implementsOnly
from zope.formlib.widgets import FileWidget
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.schema import Field

zope_ = MessageFactory("zope")


class FileUpload(Field):
    pass


class FileUploadWidget(FileWidget):

    implementsOnly(IInputWidget)
    adapts(FileUpload, IBrowserRequest)

    def _toFieldValue(self, input):
        if not input:
            return self.context.missing_value
        try:
            filename = input.filename.split('\\')[-1]  # for IE
            input.filename = filename.strip().replace(' ', '_')
        except AttributeError, e:
            raise ConversionError(zope_('Form input is not a file object'), e)
        return input

    def hasInput(self):
        return ((self.required and self.name + ".used" in self.request.form) or
                self.request.form.get(self.name))
