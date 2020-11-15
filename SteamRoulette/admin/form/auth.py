from wtforms import PasswordField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from SteamRoulette.libs.forms.base import Form
from SteamRoulette.libs.i18n import _
from SteamRoulette.models.admin_user import UserAdmin


class AdminLoginForm(Form):
    email = EmailField(label=_('Email'))
    password = PasswordField(
        label=_('Password'),
        validators=[DataRequired(message=_('Required'))],
    )
    submit = SubmitField(_("Login"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = None

    def validate(self):
        if not super().validate():
            return False

        self.user = UserAdmin.get_by_email(self.email.data)

        if self.user and self.user.check_password(self.password.data):
            return True
        else:
            self.password.errors.append(_('Password does not match'))
        return False
