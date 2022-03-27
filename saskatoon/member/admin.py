# coding: utf-8

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import (UserCreationForm, UserChangeForm,
                                        ReadOnlyPasswordHashField)
from member.models import (AuthUser, Actor, Language, Person, Organization,
                           Neighborhood, City, State, Country)
from member.filters import GroupFilter, PropertyFilter, PickLeaderFilter, VolunteerFilter
from django.contrib.auth.models import Group

class CustomUserCreationForm(UserCreationForm):
    """A form for creating new users. Includes all the required fields,
    plus a repeated password."""

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        required=False
    )
    password2 = forms.CharField(
        label='Password Confirmation',
        widget=forms.PasswordInput,
        required=False
    )

    class Meta(UserCreationForm.Meta):
        model = AuthUser
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    password = ReadOnlyPasswordHashField(
        label="password",
        help_text="""Raw passwords are not stored, so there is no way to
        see this user's password, but you can change the password using
        <a href=\"../password/\"> this form</a>."""
    )

    class Meta(UserChangeForm.Meta):
        model = AuthUser
        fields = ('email', 'password', 'is_active',
                  'is_staff', 'is_superuser', 'user_permissions')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


@admin.register(AuthUser)
class AuthUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    search_fields = ('email', 'person__first_name', 'person__family_name')
    ordering = ('email', 'person')
    filter_horizontal = ('groups', 'user_permissions',)
    list_display = ('email',
                    'person',
                    'get_groups',
                    'is_staff',
                    'is_core',
                    'is_admin',
                    'is_active',
                    'id'
                    )

    def is_core(self, user):
        return user.groups.filter(name="core").exists()
    is_core.short_description = "core"
    is_core.boolean = True

    def is_admin(self, user):
        return user.is_superuser
    is_admin.short_description = "admin"
    is_admin.boolean = True

    def get_groups(self, user):
        return ' + '.join([g.name for g in user.groups.all()])
    get_groups.short_description = "group(s)"


    list_filter = (GroupFilter,
                   PropertyFilter,
                   PickLeaderFilter,
                   VolunteerFilter,
                   'is_staff',
                   'is_superuser',
                   'is_active'
                   )

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'email',
                    'password',
                    'person'
                )
            }
        ),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups'
                )
            }
        ),
    )

    add_fieldsets = (
        (
            None, {
                'classes': 'wide',
                'fields': (
                    'email',
                    'password1',
                    'password2',
                    'is_staff',
                    'is_superuser',
                    'groups'
                )
            }
        ),
    )

    # ACTIONS
    def clear_groups(self, request, queryset):
        for u in queryset:
            u.groups.clear()
            u.is_superuser = False
            u.is_staff = False
            u.save()

    def add_to_staff(self, user):
        user.is_staff = True
        user.save()

    def add_to_group(self, user, name):
        group, __ = Group.objects.get_or_create(name=name)
        user.groups.add(group)

    def add_to_admin(self, request, queryset):
        for u in queryset:
            self.add_to_group(u, 'admin')
            u.is_superuser = True
            self.add_to_staff(u)

    def add_to_core(self, request, queryset):
        for u in queryset:
            self.add_to_group(u, 'core')
            self.add_to_staff(u)

    def add_to_pickleader(self, request, queryset):
        for u in queryset:
            self.add_to_group(u, 'pickleader')
            self.add_to_staff(u)

    def add_to_volunteer(self, request, queryset):
        for u in queryset:
            self.add_to_group(u, 'volunteer')

    def add_to_owner(self, request, queryset):
        for u in queryset:
            self.add_to_group(u, 'owner')

    def deactivate_account(self, request, queryset):
        for u in queryset:
            if not u.is_superuser:
                u.is_active = False
                u.save()

    actions = [
        clear_groups,
        add_to_admin,
        add_to_core,
        add_to_pickleader,
        add_to_volunteer,
        add_to_owner,
        deactivate_account,
    ]


# admin.site.register(Notification)
# admin.site.register(AuthUserAdmin)
admin.site.register(Actor)
admin.site.register(Language)
admin.site.register(Person)
admin.site.register(Organization)
admin.site.register(Neighborhood)
admin.site.register(City)
admin.site.register(State)
admin.site.register(Country)
