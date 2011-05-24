from butter import forms
from django.forms.formsets import BaseFormSet 
from django.forms.models import modelformset_factory
from testproject.notes.models import Note, Tag 

visibility_relation = modelformset_factory(Tag.visible_to_members.through)

class TagForm(forms.Form):
    tag_name = forms.CharField()
    is_public = forms.BooleanField(required=False, initial=True)

    @forms.varies_on('is_public')
    def visible_to(self, is_public):
        if is_public:
            return forms.RelatedForm(visibility_relation)
        else:
            return forms.BooleanField(help_text='Are you sure?')

    def __init__(self, note, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)
        self.note = note

class TagFormSet(BaseFormSet):
    max_num = None
    extra = 1
    can_order = False
    can_delete = True

    def __init__(self, note, *args, **kwargs):
        self.note = note
        super(TagFormSet, self).__init__(*args, **kwargs)

    def form(self, *args, **kwargs):
        return TagForm(self.note, *args, **kwargs)

class NoteForm(forms.Form):
    title = forms.CharField()
    description = forms.CharField(widget=forms.Textarea)
    tags = forms.RelatedForm(TagFormSet, passing_kwargs={'note':'note'})

    def __init__(self, note=None, *args, **kwargs):
        super(NoteForm, self).__init__(*args, **kwargs)
        self.note = note
