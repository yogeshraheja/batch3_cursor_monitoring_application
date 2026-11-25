"""WTForms with CSRF for login and inventory mutations."""

from __future__ import annotations

import re

from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    PasswordField,
    RadioField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

# Hostnames / IPs only — reject shell metacharacters and whitespace abuse.
_HOST_RE = re.compile(
    r"^(?=.{1,255}$)"
    r"(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"|(?:\d{1,3}\.){3}\d{1,3}"
    r"|\[?[A-Fa-f0-9:]+\]?)$"
)
_UNSAFE_HOST_CHARS = re.compile(r"[;&|`$<>\\\n\r\t \"']")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=256)])
    submit = SubmitField("Sign in")


class ServerForm(FlaskForm):
    name = StringField("Display name", validators=[DataRequired(), Length(max=120)])
    host = StringField("Host", validators=[DataRequired(), Length(max=255)])
    ssh_port = IntegerField(
        "SSH port",
        default=22,
        validators=[InputRequired(), NumberRange(min=1, max=65535)],
    )
    ssh_username = StringField(
        "SSH username", validators=[DataRequired(), Length(max=120)]
    )
    auth_type = RadioField(
        "Auth method",
        choices=[("password", "Password"), ("key", "Private key")],
        default="password",
        validators=[DataRequired()],
    )
    # Sensitive: demo-only storage in local SQLite.
    ssh_password = PasswordField("SSH password", validators=[Optional(), Length(max=512)])
    private_key_path = StringField(
        "Private key path (on this host)",
        validators=[Optional(), Length(max=512)],
    )
    private_key_content = TextAreaField(
        "Or paste private key",
        validators=[Optional(), Length(max=16384)],
    )
    submit = SubmitField("Add server")

    def validate_host(self, field: StringField) -> None:
        value = (field.data or "").strip()
        if _UNSAFE_HOST_CHARS.search(value) or not _HOST_RE.match(value):
            raise ValidationError(
                "Host must be a hostname or IP without shell metacharacters."
            )
        field.data = value

    def validate(self, extra_validators: dict | None = None) -> bool:
        is_valid = super().validate(extra_validators=extra_validators)
        if not is_valid:
            return False

        auth_type = self.auth_type.data
        if auth_type == "password":
            if not (self.ssh_password.data or "").strip():
                self.ssh_password.errors.append("Password is required for password auth.")
                return False
        elif auth_type == "key":
            has_path = bool((self.private_key_path.data or "").strip())
            has_content = bool((self.private_key_content.data or "").strip())
            if not has_path and not has_content:
                self.private_key_path.errors.append(
                    "Provide a key path (preferred) or paste a private key."
                )
                return False
        return True


class DeleteServerForm(FlaskForm):
    submit = SubmitField("Remove")
