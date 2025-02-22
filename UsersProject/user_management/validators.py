from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re
from .models import PasswordPolicy

class PasswordPolicyValidator:
    """
    Validate password according to the current password policy settings.
    """
    def __init__(self):
        self.policy = None

    def get_policy(self):
        if not self.policy:
            self.policy = PasswordPolicy.get_policy()
        return self.policy

    def validate(self, password, user=None):
        policy = self.get_policy()

        if len(password) < policy.min_length:
            raise ValidationError(
                _(f'Password must be at least {policy.min_length} characters long.'),
                code='password_too_short',
            )

        if policy.require_uppercase and not any(c.isupper() for c in password):
            raise ValidationError(
                _('Password must contain at least one uppercase letter.'),
                code='password_no_upper',
            )

        if policy.require_lowercase and not any(c.islower() for c in password):
            raise ValidationError(
                _('Password must contain at least one lowercase letter.'),
                code='password_no_lower',
            )

        if policy.require_numbers and not any(c.isdigit() for c in password):
            raise ValidationError(
                _('Password must contain at least one number.'),
                code='password_no_number',
            )

        if policy.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _('Password must contain at least one special character: !@#$%^&*(),.?":{}|<>'),
                code='password_no_special',
            )

    def get_help_text(self):
        policy = self.get_policy()
        help_text = [f'Your password must be at least {policy.min_length} characters long.']
        
        if policy.require_uppercase:
            help_text.append('Your password must contain at least one uppercase letter.')
        if policy.require_lowercase:
            help_text.append('Your password must contain at least one lowercase letter.')
        if policy.require_numbers:
            help_text.append('Your password must contain at least one number.')
        if policy.require_special_chars:
            help_text.append('Your password must contain at least one special character: !@#$%^&*(),.?":{}|<>')
        
        return ' '.join(help_text)
