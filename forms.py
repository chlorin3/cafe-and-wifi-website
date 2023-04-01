from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    PasswordField,
    BooleanField,
    SelectField,
    TextAreaField,
    TelField,
    EmailField,
    DecimalField,
)
from wtforms.validators import DataRequired, URL, Email, EqualTo, Regexp, Length


class AddCafeForm(FlaskForm):
    name = StringField("Cafe name", validators=[DataRequired(), Length(min=2, max=50)])
    map_url = StringField("Map URL", validators=[DataRequired(), URL()])
    location = StringField("Location", validators=[DataRequired()])
    img_url = StringField("Image URL", validators=[DataRequired(), URL()])
    seats = SelectField(
        "Number of seats",
        choices=["0-10", "10-20", "20-30", "30-40", "40-50", "50+"],
        validators=[DataRequired()],
    )
    has_toilet = BooleanField("Toilet")
    has_wifi = BooleanField("Wifi")
    has_sockets = BooleanField("Sockets")
    can_take_calls = BooleanField("Can take calls")
    coffee_price = DecimalField("Coffee price", validators=[DataRequired()])
    submit = SubmitField("Submit Cafe")


class ContactUsForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField(
        "Email Address", validators=[DataRequired(), Length(min=2, max=50)]
    )
    phone_number = TelField(
        "Phone number",
        validators=[
            Regexp(
                regex=r"^((\+[0-9]{0,4}) [0-9]{4,13})?$",
                message="Invalid input. Example: +44 1234567899",
            )
        ],
    )
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Send")


class LoginForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=2, max=50)]
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(max=50)])
    submit = SubmitField("Let me in!")


class RegisterForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(), Email(), Length(min=2, max=50)]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=50),
            EqualTo("password_confirm", message="Passwords must match"),
        ],
    )
    password_confirm = PasswordField("Repeat Password", validators=[DataRequired()])
    submit = SubmitField("Sign me up!")
