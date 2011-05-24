from django.shortcuts import render
from testproject.notes.forms import NoteForm
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def create_note(request):
    if request.method == 'POST':
        form = NoteForm(None, request.POST)
        if form.is_valid():
            return None
    else:
        form = NoteForm(None)

    resp = '<form method="POST" action=".">%s<input type="submit" value="submit" /></form>' % form
    return HttpResponse(resp)
