from django import forms
from django.forms.widgets import media_property
from django.utils.datastructures import SortedDict
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from butter.fields import VaryingField, RelatedForm
from butter.widgets import RelatedFormWidget

# Fun fact! ``__all__`` is literally my least favorite thing about Python.
# We owe the fact that we can't directly subclass ``BoundField`` to it.
# So, we work around it, like so many sappers. 
class RelatedFormBoundFieldBase(object):
    """
        The RelatedFormBoundFieldBase object is the repository of knowledge
        for the ``form_class`` -- due to the way Django's form library works,
        the BoundField is pretty much perfectly positioned to be able to see into
        not only the form's member's, but also the incoming data as well as the original
        **kwargs going into the Field object.
    """
    def __init__(self, *args, **kwargs):
        super(RelatedFormBoundFieldBase, self).__init__(*args, **kwargs)
        self.passing_kwargs = getattr(self.field, 'passing_kwargs', {})
        self.form_class = getattr(self.field, 'form_class', None)

        # curry the widget creation with our ``get_form`` method. 
        self.widget = RelatedFormWidget(self.get_form) 

        if self.form_class is None:
            raise forms.ValidationError('``%s.%s.form_class`` is not defined' % (type(self.form), self.name))

    def as_widget(self, widget=None, *args, **kwargs):
        # Override the default ``as_widget`` bits so we can use our super-special
        # form-widget.
        if widget is None:
            widget = self.widget
        return super(RelatedFormBoundFieldBase, self).as_widget(widget, *args, **kwargs)

    def value(self):
        return self.widget.value_from_datadict(self.form.data or self.form.initial, self.form.files, self.form.add_prefix(self.name))

    def get_form(self, *args, **kwargs):
        updated_kwargs = {}
        for key, value in self.passing_kwargs.iteritems():
            call_function = getattr(self.form, value)
            if callable(call_function):
                # if it's a callable, call it!
                updated_kwargs[key] = callable(call_function)
            else:
                # otherwise just grab the attribute and move on.
                updated_kwargs[key] = call_function

        base_kwargs = {}
        base_kwargs.update(kwargs)
        base_kwargs.update(updated_kwargs)

        return self.form_class(*args, **base_kwargs)

class VaryingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(VaryingForm, self).__init__(*args, **kwargs)

        # so, we're iterating over ``self.base_fields`` because we want the
        # canonical CLASS-WIDE definition of what the fields are.
        #
        # however, as we're currently operating within the instance of a Form
        # class, we want to modify the existing fields available to just this
        # instance.
        #
        # so basically, we're being jerks and determining what our fields will
        # look like upon instantiation. LIKE A BOSS.
        for field_name, field in self.base_fields.items():
            if isinstance(field, VaryingField):
                self.fields[field_name] = field.determine_field(self)

class NestedForm(forms.Form):
    @classmethod
    def get_related_type(cls, bound_field):
        if hasattr(cls, '_related_type'):
            return cls._related_type

        cls._related_type = type('RelatedFormBoundField', (RelatedFormBoundFieldBase, type(bound_field)), {})
        return cls._related_type

    def _trap_bound_field(self, bound_field):
        if isinstance(bound_field.field, RelatedForm):
            bound_field_type = NestedForm.get_related_type(bound_field)
            return bound_field_type(self, bound_field.field, bound_field.name)
        return bound_field

    def __init__(self, *args, **kwargs):
        self.super = super(NestedForm, self)
        super(NestedForm, self).__init__(*args, **kwargs)

    def __getitem__(self, name):
        return self._trap_bound_field(self.super.__getitem__(name))

    def __iter__(self):
        for bound_field in self.super.__iter__():
            yield self._trap_bound_field(bound_field)

    def _clean_fields(self):
        for name, field in self.fields.items():
            if isinstance(field, RelatedForm):
                bound_field = self[name]
                value = bound_field.value()
            else:
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, forms.FileField):
                    initial = self.initial.get(name, field.initial)
                    value = field.clean(value, initial)
                else:
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except forms.ValidationError, e:
                self._errors[name] = self.error_class(e.messages)
                if name in self.cleaned_data:
                    del self.cleaned_data[name]

    # WARNING: THIS IS GROSS
    # ======================
    # I had to yank ``_html_output`` out of the BaseForm class so that
    # I could control which kind of ``BoundField`` it was attempting to create.
    #
    # Gag. A better way around this might be to ... I don't know. Stop screwing with
    # the form library, probably.
    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
        top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
        output, hidden_fields = [], []

        for name, field in self.fields.items():
            html_class_attr = ''

            # FIXME: Yes, this is the only line I changed between django's version and mine.
            # foam is coming out of my mouth right now.
            bf = self[name]
            bf_errors = self.error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
            if bf.is_hidden:
                if bf_errors:
                    top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
                hidden_fields.append(unicode(bf))
            else:
                # Create a 'class="..."' atribute if the row should have any
                # CSS classes applied.
                css_classes = bf.css_classes()
                if css_classes:
                    html_class_attr = ' class="%s"' % css_classes

                if errors_on_separate_row and bf_errors:
                    output.append(error_row % force_unicode(bf_errors))

                if bf.label:
                    label = conditional_escape(force_unicode(bf.label))
                    # Only add the suffix if the label does not end in
                    # punctuation.
                    if self.label_suffix:
                        if label[-1] not in ':?.!':
                            label += self.label_suffix
                    label = bf.label_tag(label) or ''
                else:
                    label = ''

                if field.help_text:
                    help_text = help_text_html % force_unicode(field.help_text)
                else:
                    help_text = u''

                output.append(normal_row % {
                    'errors': force_unicode(bf_errors),
                    'label': force_unicode(label),
                    'field': unicode(bf),
                    'help_text': help_text,
                    'html_class_attr': html_class_attr
                })

        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))

        if hidden_fields: # Insert any hidden fields in the last row.
            str_hidden = u''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                if not last_row.endswith(row_ender):
                    # This can happen in the as_p() case (and possibly others
                    # that users write): if there are only top errors, we may
                    # not be able to conscript the last row for our purposes,
                    # so insert a new, empty row.
                    last_row = (normal_row % {'errors': '', 'label': '',
                                              'field': '', 'help_text':'',
                                              'html_class_attr': html_class_attr})
                    output.append(last_row)
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)
        return mark_safe(u'\n'.join(output))
