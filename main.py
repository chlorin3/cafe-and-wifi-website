from functools import wraps
from flask import (
    Flask,
    url_for,
    render_template,
    redirect,
    request,
    flash,
    current_app,
    session,
    abort,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from forms import AddCafeForm, ContactUsForm, LoginForm, RegisterForm, ChangeRoleForm
from flask_login import (
    UserMixin,
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask_principal import (
    Principal,
    Permission,
    RoleNeed,
    identity_changed,
    Identity,
    AnonymousIdentity,
    UserNeed,
    identity_loaded,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"

login_manager = LoginManager()
login_manager.init_app(app)

# load the principal extension
Principal(app)
# Create a permission with a single Need, in this case a RoleNeed.
admin_permission = Permission(RoleNeed("admin"))

# Connect to Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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
    role = db.Column(db.String(250), default="user")


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
    if hasattr(current_user, "id"):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a role, update the
    # identity with the role that the user provides
    if hasattr(current_user, "role"):
        identity.provides.add(RoleNeed(current_user.role))


# Create admin_required decorator
def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        # If user doesn't have an admin role then return 403 error
        if not admin_permission.require().can():
            return abort(403)
        # Otherwise continue with the route function
        return function(*args, **kwargs)

    return wrapper


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/cafes")
def get_all_cafes():
    # Retrieve all the Cafe objects from the database
    all_cafes = db.session.execute(db.select(Cafe)).scalars().all()
    return render_template("cafes.html", cafes=all_cafes)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_cafe():
    form = AddCafeForm()
    # Check if the form has been submitted and validated
    if form.validate_on_submit():
        # Check if a cafe with this name exists and if so,
        # show and error message and redirect them to a new add cafe form.
        exists = db.session.execute(
            db.select(Cafe).filter_by(name=form.name.data.title())
        ).scalar_one_or_none()
        if exists:
            flash("This cafe already exists", "error")
            return redirect(url_for("add_cafe"))

        # Otherwise, create a new Cafe object.
        new_cafe = Cafe(
            name=form.name.data.title(),
            map_url=form.map_url.data,
            img_url=form.img_url.data,
            location=form.location.data.title(),
            seats=form.seats.data,
            has_toilet=form.has_toilet.data,
            has_wifi=form.has_wifi.data,
            has_sockets=form.has_sockets.data,
            can_take_calls=form.can_take_calls.data,
            coffee_price="£" + str(round(form.coffee_price.data, 2)),
        )

        # Add a new Cafe object to the database.
        db.session.add(new_cafe)
        db.session.commit()
        flash("Cafe successfully added!", "success")
        return redirect(url_for("add_cafe"))
    # If the form is not submitted or validated, render the add page with the form object
    else:
        return render_template("add.html", form=form)


@app.route("/cafes/<int:cafe_id>/delete")
@admin_required
def delete_cafe(cafe_id):
    # Get the Cafe object from the database using its ID.
    cafe = db.session.get(Cafe, cafe_id)
    # Check if the cafe exists in the database.
    if cafe:
        # If it does, delete the cafe from the database.
        db.session.delete(cafe)
        db.session.commit()
        # Display a success flash message to the user.
        flash("Cafe successfully deleted!", "success")
    # Redirect the user back to the page that displays all cafes.
    return redirect(url_for("get_all_cafes"))


@app.route("/cafes/<int:cafe_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_cafe(cafe_id):
    # Get the Cafe object from the database using its ID.
    cafe = db.session.get(Cafe, cafe_id)

    # Check if the cafe exists in the database.
    if not cafe:
        # If it does not, display an error flash message to the user.
        flash("This cafe does not exist!", "error")
        # Redirect the user back to the page that displays all cafes.
        return redirect(url_for("get_all_cafes"))

    # Pre-populate the AddCafeForm with the cafe's existing information
    edit_form = AddCafeForm(
        name=cafe.name,
        map_url=cafe.map_url,
        img_url=cafe.img_url,
        location=cafe.location,
        seats=cafe.seats,
        has_toilet=cafe.has_toilet,
        has_wifi=cafe.has_wifi,
        has_sockets=cafe.has_sockets,
        can_take_calls=cafe.can_take_calls,
        coffee_price=float(cafe.coffee_price.removeprefix("£")),
    )

    # If the form is submitted and passes validation, the cafe's information is updated.
    if edit_form.validate_on_submit():
        cafe.name = edit_form.name.data.title()
        cafe.map_url = edit_form.map_url.data
        cafe.img_url = edit_form.img_url.data
        cafe.location = edit_form.location.data.title()
        cafe.seats = edit_form.seats.data
        cafe.has_toilet = edit_form.has_toilet.data
        cafe.has_wifi = edit_form.has_wifi.data
        cafe.has_sockets = edit_form.has_sockets.data
        cafe.can_take_calls = edit_form.can_take_calls.data
        cafe.coffee_price = "£" + str(round(edit_form.coffee_price.data, 2))

        # Try updating the information in the database.
        try:
            db.session.commit()
        except IntegrityError:
            # If there's an integrity error when updating the cafe information, flash a warning message.
            flash(
                "Oops, something's gone wrong. This cafe may already exist!", "warning"
            )
            # Redirect the user back to the same page with the currently edited form.
            # This allows the user to make corrections to the form without losing their progress.
            return redirect(request.url)

        # If the update is successful, flash a success message and redirect the user to the page displaying all cafes.
        flash("Cafe successfully edited!", "success")
        return redirect(url_for("get_all_cafes"))
    else:
        # If the form is not submitted or validated, render the page with the edit form object and pass cafe's id.
        return render_template("add.html", form=edit_form, cafe_id=cafe_id)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactUsForm()
    # Check if the form has been submitted and validated
    if form.validate_on_submit():
        # If the form is validated, create a new message object and add it to the database.
        new_message = Message(
            name=form.name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            message=form.message.data,
        )
        db.session.add(new_message)
        db.session.commit()
        # Show a success message
        flash("Success!", "success")
        # Redirect to the contact page with a parameter indicating that the message was successfully sent
        return render_template("contact.html", is_sent=True)
    # If the form is not submitted or validated, render the contact page with the form object
    return render_template("contact.html", form=form)


# This route handler is only accessible by users with the admin role. They can view the list of messages
# sent through contact page.
@app.route("/messages")
@admin_required
def show_messages():
    # Retrieve all messages from the database and order them by date in descending order
    all_messages = (
        db.session.execute(db.select(Message).order_by(Message.date.desc()))
        .scalars()
        .all()
    )
    # Render the page, passing the retrieved messages to it
    return render_template("messages.html", messages=all_messages)


@app.route("/messages/<int:message_id>/delete")
@admin_required
def delete_message(message_id):
    # Get the message object from the database using its ID.
    message = db.session.get(Message, message_id)
    # Check if the message exists in the database.
    if message:
        # If it does, delete the message from the database.
        db.session.delete(message)
        db.session.commit()
        # Display a success flash message
        flash("Message deleted!", "success")
    # Redirect the user back to the page that displays all messages.
    return redirect(url_for("show_messages"))


@app.route("/users")
@admin_required
def get_all_users():
    # Retrieve all users from the database
    all_users = db.session.execute(db.select(User)).scalars().all()
    # Create a pre-populated form for each user
    change_role_forms = [
        ChangeRoleForm(user_id=user.id, role=user.role) for user in all_users
    ]
    # Create a list with (user, form) tuples
    user_form_tuples = zip(all_users, change_role_forms)
    # Render the page, passing the retrieved users with forms to it
    return render_template("users.html", users=user_form_tuples)


@app.route("/users/<int:user_id>/delete")
@admin_required
def delete_user(user_id):
    # Get the user from the database using their ID.
    user = db.session.get(User, user_id)
    # Check if the user exists in the database.
    if user:
        # If it does, delete the user from the database.
        db.session.delete(user)
        db.session.commit()
        # Display a success flash message
        flash("User deleted!", "success")
    # Redirect the user back to the page that displays all users.
    return redirect(url_for("get_all_users"))


@app.route("/users", methods=["POST"])
@admin_required
def change_user_role():
    form = ChangeRoleForm()
    # Get the user from the database using their ID.
    user = db.session.get(User, form.user_id.data)
    # Check if the user exists in the database and if form passed validation on submit
    if user and form.validate_on_submit():
        # Update user's role
        user.role = form.role.data
        # Commit changes in the database
        db.session.commit()
        flash("User role updated successfully.", "success")
    return redirect(url_for("get_all_users"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # Generate a hash of the password
        password_hash = generate_password_hash(form.password.data)
        # Create a new user with the submitted email and hashed password
        new_user = User(email=form.email.data, password=password_hash)
        # Add the new user to the database
        db.session.add(new_user)

        # Attempt to commit the changes to the database
        try:
            db.session.commit()
        # If the email address already exists in the database, flash an error message
        # and redirect back to the registration page.
        except IntegrityError:
            flash("You already have an account!", "error")
            return redirect(request.url)

        # If the changes are successfully committed to the database,
        # flash a success message, log the user in, and redirect to the home page
        flash("Your account was successfully created", "success")
        login_user(new_user)
        return redirect(url_for("home"))

    # If the form has not been submitted or does not pass validation, render the registration form
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    # Check if the form is submitted and valid
    if form.validate_on_submit():
        # Find the user with the email address entered in the form
        user = db.session.execute(
            db.select(User).filter_by(email=form.email.data)
        ).scalar_one_or_none()
        # Check if the user exists and the password entered matches the hashed password in the database
        if user and check_password_hash(user.password, form.password.data):
            # Log the user in
            login_user(user)

            # Set user identity
            identity_changed.send(
                current_app._get_current_object(), identity=Identity(user.id)
            )

            # Flash a success message and redirect to the home page
            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))
        else:
            # Flash an error message if the email or password is incorrect
            flash("Wrong credentials!", "error")
    # Render the login page with the login form
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    # Log the user out
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ("identity.name", "identity.auth_type"):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )

    # Flash a success message and redirect to the home page
    flash("You've been logged out", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
