from django.http import HttpRequest

def is_admin_processor(request:HttpRequest):
    if request.user.is_authenticated:
        return {'is_admin': request.user.groups.filter(name='Admin').exists()}
    return {'is_admin': False}