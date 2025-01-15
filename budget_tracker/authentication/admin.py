from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    # Fields to display in the admin interface
    list_display = ('email', 'name', 'phone', 'is_admin', 'is_active')
    list_filter = ('is_admin', 'is_active')
    
    # Fieldsets for editing user details
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'phone')}),
        ('Permissions', {'fields': ('is_admin', 'is_active', 'groups', 'user_permissions')}),
    )
    
    # Fields for creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone', 'password1', 'password2', 'is_active', 'is_admin'),
        }),
    )
    
    search_fields = ('email', 'name', 'phone')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')

# Register the custom User model and its admin interface
admin.site.register(User, UserAdmin)
