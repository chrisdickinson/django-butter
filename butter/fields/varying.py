from django import forms

class VaryingField(forms.Field):
    def __init__(self, crucible, varying_on_field, *args, **kwargs):
        self.crucible = crucible
        self.varying_on_field = varying_on_field
        self.curried_args = args
        self.curried_kwargs = kwargs

    def determine_field(self, form):
        value = form[self.varying_on_field].value()
        return self.crucible(form, value, *self.curried_args, **self.curried_kwargs)


def varies_on(what_name, *args, **kwargs):
    def inner(fn):
        return VaryingField(fn, what_name, *args, **kwargs)
    return inner
