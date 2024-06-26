"""
    Routes
    ~~~~~~
"""
import os
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask import current_app
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from .forms import AssignRoleForm
from .forms import LoginForm

from wiki.core import Processor
from wiki.web.forms import EditorForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect


bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')
"""add code"""
@bp.route('/instructions/')
@protect
def instructions():
    return render_template('instructions.html')

@bp.route('/admin')
@login_required
def admin():
    print(roles)
    if current_user.has_role('admin'):
        current_user.clear_all_roles()
        return render_template('admin.html')
    else:
        flash('You do not have access to this page.', 'error')
        return redirect(url_for('wiki.index'))



@bp.route('/roles/', methods=['GET', 'POST'])
@protect
def roles():
    form = AssignRoleForm()
    assigned_role = None
    if form.validate_on_submit():
        username = form.username.data
        role = form.role.data
        user = current_users.get_user(username)
        if user:
            user_roles = user.get('roles', [])
            user_roles.append(role)
            user.set('roles', user_roles)
            flash(f'Role "{role}" assigned to user "{username}".', 'success')
            assigned_role = role
            print("Assigned role:", assigned_role)
            return redirect(url_for('wiki.user_index'))
        else:
            flash('User not found.', 'error')
    print("Assigned role:", assigned_role)
    return render_template('roles.html', form=form, assigned_role=assigned_role)


@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)


@bp.route('/<path:url>/')
@protect
def display(url):
    page = current_wiki.get_or_404(url)
    custom_css_exists = os.path.exists(os.path.join(current_app.static_folder, f"{url}.css"))
    return render_template('page.html', page=page, custom_css_exists=custom_css_exists)


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        css_filename = f"{url}.css"
        css_path = os.path.join(current_app.static_folder, css_filename)
        if form.text_color.data and form.background_color.data:
            with open(css_path, 'w') as f:
                f.write(f"""
                    /* {css_filename} */
                    body {{
                        color: {form.text_color.data};
                        background-color: {form.background_color.data};
                    }}
                """)
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    current_wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))


@bp.route('/user/')
def user_index():
    return redirect(url_for('wiki.index'))
    # pass


@bp.route('/user/create/')
def user_create():
    pass


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

