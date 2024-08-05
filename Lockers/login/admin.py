from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin

# Register your models here.

class CustomeUserAdmin(UserAdmin):
    list_display = ["username", "name","email","phone"]
    add_fieldsets = (
        (
            "인증정보",
            {
                "fields" : ("username", "password1","password2"),
            }
        ),
        (
            "개인정보",
            {
                "fields": ("name","email","phone")
            }
        )
    )
    fieldsets = (
        (
            "인증정보",
            {
                "fields" : ("username", "password")
            }
        ),
        (
            "개인정보",
            {
                "fields" : ("name","email","phone")
            }
        ),
        (
            "권한",
            {
                "fields" : ("is_active" , "is_superuser")
            }
        )
    )

admin.site.register(User,CustomeUserAdmin)