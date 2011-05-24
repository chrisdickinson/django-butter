Django-Butter
=============

All the fun of django forms, now with added broken!

**Seriously, this is pretty proof of concept at the moment.**

What Can Butter Do For Me?
-------------

Butter aims to pave over some rough spots in the Django form library --
notably, it adds decorators for being able to vary a given field based on a 
previous field, like so:

    from butter import forms

    class MyForm(forms.Form):
        my_name = forms.CharField(max_length=100)

        @forms.varies_on('my_name')
        def my_rating(self, my_name):
            if my_name == 'Gary Busey':
                return forms.IntegerField(min_value=80, max_value=100)
            else:
                return forms.IntegerField(min_value=0, max_value=100)

Depending on the value of ``my_name`` when the form is submitted, the next
field will be validated differently. There's no law that says you have to keep
the returned field types the same, either; however, you must realize that ``butter``
isn't going to be able to solve the halting problem just so it can figure out what
HTML to show with your form -- you'll have to think of a way to do that yourself.

Well That's Disheartening
-------------

Don't worry! There's more! Butter's other goal is to provide you with the ability
to nest forms like a pro! Let's take a look:

    from django.forms.models import modelformset_factory
    from butter import forms

    UserFormSet = modelformset_factory(User, extra=2)

    class LocationForm(forms.Form):
        where = forms.CharField()
        when = forms.DateTimeField()

    class FlashMobForm(forms.Form):
        event_name = forms.CharField()
        event_location = forms.RelatedForm(LocationForm)
        attendees = forms.RelatedForm(UserFormSet)

Okay, but how do I use it? LOOK NO FURTHER THAN SEVERAL PIXELS BELOW THIS LINE:

    from flashmob.forms import FlashMobForm

    def flash_mob_create(request):
        form = FlashMobForm(request.POST or None)
        if form.is_valid():
            # you now have access to ``form.cleaned_data``!
            # it will look like the following:
            {
                event_name:<string>,
                event_location:{
                    where:<string>,
                    when:<datetime>
                },
                attendees:[<user>, <user>, <user>]
            }
            return redirect('someplace-safe')
        # and it renders like a normal form too!
        return HttpResponse('<form method="POST" action=".">%s<input type="submit" value="submit" /></form>' % form)

It's like magic!

Being facetious about the code quality of this project aside; I do intend to clean it up and unit test it thoroughly -- this is just the first
cut to see if I can etch out an API that I like; not to mention to see if such a thing is even feasible.

That being said, it's licensed BSD.
