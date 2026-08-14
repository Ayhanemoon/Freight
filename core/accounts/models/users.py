from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from freight.models import Branch
from phonenumber_field.modelfields import PhoneNumberField
import phonenumbers

class UserManager(BaseUserManager):
    """
    Custom user model manager where mobile is the unique identifiers
    for authentication instead of usernames.
    """

    def normalize_mobile(self, mobile):
        if not mobile:
            raise ValueError(_("The Mobile must be set"))

        try:
            # Default region can be changed later
            phone = phonenumbers.parse(str(mobile), "IR")

            if not phonenumbers.is_valid_number(phone):
                raise ValidationError(_("Invalid mobile number"))

            # Return E.164 format, e.g. +989121234567
            return phonenumbers.format_number(
                phone,
                phonenumbers.PhoneNumberFormat.E164,
            )

        except phonenumbers.NumberParseException:
            raise ValidationError(_("Invalid mobile number format"))

    def create_user(self, mobile, password, **extra_fields):
        """
        Create and save a User with the given mobile and password.
        """
        if not mobile:
            raise ValueError(_("The Mobile must be set"))
        mobile = self.normalize_mobile(mobile)
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, mobile, password, **extra_fields):
        """
        Create and save a SuperUser with the given mobile and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_mobile_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(mobile, password, **extra_fields)


AUTH_PROVIDERS = {
    "facebook": "facebook",
    "google": "google",
    "twitter": "twitter",
    "email": "email",
    "mobile": "mobile",
}


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that uses mobile as the unique identifier."""
    
    mobile = PhoneNumberField(unique=True, db_index=True)
    email = models.EmailField(_("email address"))
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_mobile_verified  = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auth_provider = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        default=AUTH_PROVIDERS.get("mobile"),
    )

    USERNAME_FIELD = "mobile"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return str(self.mobile)
