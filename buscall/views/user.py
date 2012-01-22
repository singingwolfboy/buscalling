from buscall import app
from flask import request, redirect, url_for, flash, render_template, abort
from .util import render_json
from buscall.models.user import User
from buscall.forms import UserForm
from buscall.decorators import login_required
from ndb import Key
from google.appengine.api import users

__all__ = ['user_show', 'user_edit', 'user_update']

@login_required
@app.route('/users/<int:user_id>')
def user_show(user_id):
    user_key = Key(User, user_id)
    user = user_key.get()
    if not user:
        abort(404)
    return render_json(user)

@app.route('/users/<int:user_id>/listeners')
def listeners_for_user(user_id):
    user_key = Key(User, user_id)
    user = user_key.get()
    if not user:
        abort(404)
    return render_json(user.listeners)

@login_required
@app.route('/users/<int:user_id>/edit')
def user_edit(user_id):
    user_key = Key(User, user_id)
    user = user_key.get()
    if not user:
        abort(404)
    if not user.matches_current_google_user():
        abort(401)
    form = UserForm(request.form, user)
    return render_template("users/edit.html", form=form)

@login_required
@app.route('/users/<int:user_id>', methods=["PUT"])
def user_update(user_id):
    user_key = Key(User, user_id)
    user = user_key.get()
    if not user:
        abort(404)
    current_google_user = users.get_current_user()
    if current_google_user and current_google_user.user_id() != user.google_id:
        abort(401)
    form = UserForm(request.form, user)
    if form.validate_on_submit():
        for field_name, value in form.data.items():
            if value:
                setattr(user, field_name, value)
            else:
                setattr(user, field_name, None)
            user.put()
        flash("User updated!", category="success")
        return redirect(url_for('lander'), 303)
    else:
        flash("User update failed", category="error")
        return redirect(url_for('user_edit', user_id=user.id), 303)
