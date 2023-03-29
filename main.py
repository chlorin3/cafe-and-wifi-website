from flask import Flask, url_for, render_template, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

from forms import AddCafeForm, ContactUsForm, LoginForm, RegisterForm
from flask_login import UserMixin, LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

login_manager = LoginManager()
login_manager.init_app(app)

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

    def to_dict(self):
        # Loop through each column in the data record and create a new dictionary entry;
        # where the key is the name of the column and the value is the value of the column
        dictionary = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return dictionary


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250))

# with app.app_context():
#     db.create_all()
# exit()


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
def delete_cafe(cafe_id):
    print(cafe_id)
    cafe = db.session.get(Cafe, cafe_id)
    if cafe:
        db.session.delete(cafe)
        db.session.commit()
        flash("Cafe successfully deleted!", "success")
    return redirect(url_for("get_all_cafes"))


@app.route("/edit-cafe/<int:cafe_id>", methods=["GET", "POST"])
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
        pass
    return render_template("contact.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        pass
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    return render_template("login.html", form=form)


if __name__ == '__main__':
    app.run(debug=True)
