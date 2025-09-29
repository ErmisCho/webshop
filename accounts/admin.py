from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile
from django.utils.html import format_html
# Register your models here.


class AccountAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name',
                    'username', 'last_login', 'is_active')

    list_display_links = ('email', 'first_name', 'last_name')
    search_fields = ('email', 'username', 'last_name')
    ordering = ('-date_joined',)

    readonly_fields = ('last_login', 'date_joined')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "thumbnail", "city", "country")

    def thumbnail(self, obj):
        return format_html(
            '<img src="{}" width="30" style="border-radius:50%;">',
            obj.avatar_url  # <-- safe one-liner
        )
    thumbnail.short_description = "Avatar"


admin.site.register(Account, AccountAdmin)
