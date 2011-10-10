from buscall import app
from flask import request, redirect, url_for, flash, render_template
from buscall.models.profile import UserProfile
from buscall.forms import UserProfileForm
from buscall.decorators import login_required

@login_required
@app.route('/profiles/<profile_id>')
def edit_profile(profile_id):
    profile = UserProfile.get_by_key_name(profile_id)
    if not profile:
        abort(404)
    curr_profile = UserProfile.get_current_profile()
    if profile != curr_profile:
        abort(401)
    form = UserProfileForm(request.form, profile)
    return render_template("profiles/edit.html", form=form)

@login_required
@app.route('/profiles/<profile_id>', methods=["PUT"])
def update_profile(profile_id):
    profile = UserProfile.get_by_key_name(profile_id)
    if not profile:
        abort(404)
    curr_profile = UserProfile.get_current_profile()
    if profile != curr_profile:
        abort(401)
    form = UserProfileForm(request.form, profile)
    if form.validate_on_submit():
        for field_name, value in form.data.items():
            if value:
                setattr(profile, field_name, value)
            else:
                setattr(profile, field_name, None)
            profile.put()
        flash("Profile updated!", category="success")
        return redirect(url_for('lander'), 303)
    else:
        flash("Profile update failed", category="error")
        return render_template("profiles/edit.html", form=form)
