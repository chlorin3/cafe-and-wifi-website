from functools import wraps
from flask import Flask, url_for, render_template, redirect, request, flash, current_app, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from forms import AddCafeForm, ContactUsForm, LoginForm, RegisterForm
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_principal import Principal, Permission, RoleNeed, identity_changed, Identity, AnonymousIdentity, UserNeed, \
    identity_loaded

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

login_manager = LoginManager()
login_manager.init_app(app)

# load the principal extension
Principal(app)

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250))
    role = db.Column(db.String(250))


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    phone_number = db.Column(db.String(250))
    message = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, nullable=False, server_default=func.now())


# with app.app_context():
#     db.create_all()
# exit()


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'role'):
        identity.provides.add(RoleNeed(current_user.role))


# Create a permission with a single Need, in this case a RoleNeed.
admin_permission = Permission(RoleNeed("admin"))


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not admin_permission.require().can():
            abort(403)
        return function(*args, **kwargs)
    return wrapper


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/all", methods=["GET"])
def get_all_cafes():
    all_cafes = db.session.execute(db.select(Cafe)).scalars().all()
    return render_template("cafes.html", cafes=all_cafes)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_cafe():
    form = AddCafeForm()
    if form.validate_on_submit():
        exists = db.session.execute(db.select(Cafe).filter_by(name=form.name.data.title())).scalar_one_or_none()
        if exists:
            flash("This cafe already exists", "error")
            return redirect(url_for("add_cafe"))

        new_cafe = Cafe(name=form.name.data.title(),
                        map_url=form.map_url.data,
                        img_url=form.img_url.data,
                        location=form.location.data.title(),
                        seats=form.seats.data,
                        has_toilet=form.has_toilet.data,
                        has_wifi=form.has_wifi.data,
                        has_sockets=form.has_sockets.data,
                        can_take_calls=form.can_take_calls.data,
                        coffee_price="£" + str(round(form.coffee_price.data, 2)))
        db.session.add(new_cafe)
        db.session.commit()
        flash("Cafe successfully added!", "success")
        return redirect(url_for("add_cafe"))
    else:
        return render_template("add.html", form=form)


@app.route("/delete-cafe/<int:cafe_id>")
@admin_required
def delete_cafe(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)
    if cafe:
        db.session.delete(cafe)
        db.session.commit()
        flash("Cafe successfully deleted!", "success")
    return redirect(url_for("get_all_cafes"))


@app.route("/edit-cafe/<int:cafe_id>", methods=["GET", "POST"])
@admin_required
def edit_cafe(cafe_id):
    cafe = db.session.get(Cafe, cafe_id)
    if not cafe:
        flash("This cafe does not exist!", "error")
        return redirect(url_for("get_all_cafes"))

    form = AddCafeForm(
        name=cafe.name,
        map_url=cafe.map_url,
        img_url=cafe.img_url,
        location=cafe.location,
        seats=cafe.seats,
        has_toilet=cafe.has_toilet,
        has_wifi=cafe.has_wifi,
        has_sockets=cafe.has_sockets,
        can_take_calls=cafe.can_take_calls,
        coffee_price=float(cafe.coffee_price.removeprefix("£"))
    )

    if form.validate_on_submit():
        cafe.name = form.name.data.title()
        cafe.map_url = form.map_url.data
        cafe.img_url = form.img_url.data
        cafe.location = form.location.data.title()
        cafe.seats = form.seats.data
        cafe.has_toilet = form.has_toilet.data
        cafe.has_wifi = form.has_wifi.data
        cafe.has_sockets = form.has_sockets.data
        cafe.can_take_calls = form.can_take_calls.data
        cafe.coffee_price = "£" + str(round(form.coffee_price.data, 2))

        try:
            db.session.commit()
        except IntegrityError:
            flash("Oops, something's gone wrong. This cafe may already exist!", "warning")
            return redirect(request.url)

        flash("Cafe successfully edited!", "success")
        return redirect(url_for("get_all_cafes"))
    else:
        return render_template("edit_cafe.html", form=form, cafe_id=cafe_id)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactUsForm()
    if form.validate_on_submit():
        new_message = Message(name=form.name.data, email=form.email.data, phone_number=form.phone_number.data, message=form.message.data)
        db.session.add(new_message)
        db.session.commit()
        flash("Success!", "success")
        return render_template("contact.html", is_sent=True)
    return render_template("contact.html", form=form)


@app.route("/messages")
@admin_required
def show_messages():
    all_messages = db.session.execute(db.select(Message).order_by(Message.date.desc())).scalars().all()
    return render_template("messages.html", messages=all_messages)


@app.route("/delete-message/<int:message_id>")
@admin_required
def delete_message(message_id):
    message = db.session.get(Message, message_id)
    if message:
        db.session.delete(message)
        db.session.commit()
        flash("Message deleted!", "success")
    return redirect(url_for("show_messages"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        password_hash = generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, password=password_hash)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            flash("You already have an account!", "error")
            return redirect(request.url)
        flash("Your account was successfully created", "success")
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)

            identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))
        else:
            flash("Wrong credentials!", "error")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())

    flash("You've been logged out", "success")
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
