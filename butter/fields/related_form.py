from django import forms

class RelatedForm(forms.Field):
    def __init__(self, form_class, passing_kwargs={}, *args, **kwargs):
        super(RelatedForm, self).__init__(*args, **kwargs)
        self.form_class = form_class
        self.passing_kwargs = passing_kwargs

    def clean(self, form):
        # we receive a full-blown instantiated and bound form object from our widget.
        # all we have to do here is tell it to validate itself!
        if form.is_valid():
            # you can get into interesting situations with formsets -- they may believe they're
            # valid, but a ``delete`` button may be marked and they may not actually have 'cleaned_data'.
            if hasattr(form, 'cleaned_data'):
                return form.cleaned_data
            else:
                return {}

        # FIXME: this shouldn't display python-repr-style errors to the user. it will scare them.
        raise forms.ValidationError(str(form.errors))
