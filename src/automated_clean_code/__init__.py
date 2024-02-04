from datetime import datetime
from typing import Union

from dateutil.relativedelta import relativedelta
from flask import Flask, Response, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///leave_request.db"
app.config["SECRET_KEY"] = "myverysecretkey"
db = SQLAlchemy(app)


class User(db.Model):
    """User model.

    This class represents the User model in the database.
    """

    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    requests = db.relationship("LeaveRequest", backref="user", lazy=True)

    def __repr__(self) -> str:
        """Return a string representation of the User."""
        return f"<User {self.user_id}>"


class LeaveRequest(db.Model):
    """LeaveRequest model."""

    __tablename__ = "leave_request"
    id = db.Column(db.Integer, primary_key=True)

    reason = db.Column(db.String(200), nullable=False)
    date_start = db.Column(db.DateTime, nullable=False)
    date_end = db.Column(db.DateTime, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the LeaveRequest."""
        return f"<LeaveRequest {self.id}>"


def create_app() -> tuple[Flask, SQLAlchemy]:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///leave_request.db"
    app.config["SECRET_KEY"] = "myverysecretkey"
    db = SQLAlchemy(app)

    return app, db


@app.route("/", methods=["POST", "GET"])
def index() -> Union[str, "Response"]:
    """Render index page."""
    if "logged_in" not in session or not session["logged_in"]:
        return redirect("/login")

    user_id = session.get("user_id")

    if request.method == "POST":
        leave_reason = request.form["reason"]
        leave_date_start_str = request.form["date_start"]
        leave_date_end_str = request.form["date_end"]
        try:
            leave_date_start = datetime.strptime(leave_date_start_str, "%Y-%m-%d")
            leave_date_end = datetime.strptime(leave_date_end_str, "%Y-%m-%d")
        except ValueError:
            return "Please enter valid dates"

        # Check if leave request is more than 2 months in advance
        two_months_in_advance = datetime.now() + relativedelta(months=2)
        if leave_date_start > two_months_in_advance:
            return "You cannot request leave more than 2 months in advance"

        user_leave_requests = LeaveRequest.query.filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.date_start >= datetime(datetime.now().year, 1, 1),
            LeaveRequest.date_end <= datetime(datetime.now().year, 12, 31),
        ).all()

        total_leave_days_taken = sum((leave.date_end - leave.date_start).days + 1 for leave in user_leave_requests)

        remaining_leave_days = 10 - total_leave_days_taken

        if (leave_date_end - leave_date_start).days > remaining_leave_days:
            return f"You have only {remaining_leave_days} days left for leave this year"

        overlapping_leave_request = LeaveRequest.query.filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.date_start <= leave_date_end.replace(hour=23, minute=59, second=59),
            LeaveRequest.date_end >= leave_date_start.replace(hour=0, minute=0, second=0),
        ).first()

        if overlapping_leave_request:
            return "You have already requested leave for overlapping dates"

        new_leave = LeaveRequest(
            reason=leave_reason, date_start=leave_date_start, date_end=leave_date_end, user_id=user_id
        )

        try:
            db.session.add(new_leave)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            print(f"Error: {e}")
            return "There was an issue adding your task"
    else:
        leaves = LeaveRequest.query.order_by(LeaveRequest.date_created).all()
        return render_template("index.html", leaves=leaves)


@app.route("/login", methods=["POST", "GET"])
def login() -> Union[str, "Response"]:
    """Render login page."""
    if request.method == "POST":
        user_name = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(user_name=user_name, password=password).first()
        if user:
            session["logged_in"] = True
            session["user_id"] = user.user_id
            return redirect("/")
        else:
            return "Invalid username or password"
    else:
        return render_template("login.html")


@app.route("/register", methods=["POST", "GET"])
def register() -> Union[str, "Response"]:
    """Render register page."""
    if request.method == "POST":
        user_name = request.form["username"]
        password = request.form["password"]

        # Check if the username already exists
        existing_user = User.query.filter_by(user_name=user_name).first()
        if existing_user:
            return "Username already exists. Please choose a different username."

        new_user = User(user_name=user_name, password=password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            print(f"Error: {e}")
            return "There was an issue registering your account"
    else:
        return render_template("register.html")


@app.route("/logout")
def logout() -> Response:
    """Logout user."""
    session.pop("logged_in", None)
    session.pop("user_id", None)
    return redirect("/login")


@app.route("/delete/<int:id>")
def delete(id: int) -> Union[str, "Response"]:
    """Delete leave request."""
    leave_to_delete = LeaveRequest.query.get_or_404(id)

    if leave_to_delete.user_id == session.get("user_id"):
        if leave_to_delete.date_end >= datetime.now():
            try:
                db.session.delete(leave_to_delete)
                db.session.commit()
                return redirect("/")
            except Exception as e:
                print(f"Error: {e}")
                return "There was an issue deleting your task"
        else:
            return "You cannot delete a leave request whose end date has already passed"
    else:
        return "You do not have permission to delete this request"


if __name__ == "__main__":
    app.run(port=9042)
