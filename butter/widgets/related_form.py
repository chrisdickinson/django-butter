from django.forms import widgets

class RelatedFormWidget(widgets.Widget):
    def __init__(self, create_form, attrs=None):
        """
            RelatedFormWidgets get instantiated with a ``create_form`` function
            that helps them instantiate the form class when it's time to do so (rendering, grabbing values)
        """
        self.create_form = create_form
        super(RelatedFormWidget, self).__init__(attrs)

    def value_from_datadict(self, data, files, name):
        """
            RelatedFormWidget returns a bound form from ``value_from_datadict``, as the form object
            is the only thing that knows how to do later validation on the incoming data.
        """
        # only grab data and files that start with our name
        incoming_data = {}
        for key, value in data.iteritems():
            if key.startswith(name):
                incoming_data[key] = value

        incoming_files = {}
        for key, value in files.iteritems():
            if key.startswith(name):
                incoming_data[key] = value

        # if we don't have any incoming_data or incoming_files, be sure to pass in ``None`` or
        # the child form will think it's bound (when it's really not!)
        form = self.create_form(data=incoming_data or None, files=incoming_files or None, prefix=name)

        # Bye for now, lovely little form! We'll see you again later in ``butter.fields.related_form.RelatedForm.clean``! 
        return form

    def render(self, name, value, attrs={}):
        # Yeah! Default to <p> tags!
        return value.as_p()
