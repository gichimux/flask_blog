from datetime import datetime
from flask import g
from flask_login import login_required, current_user
from flask import render_template, redirect, url_for, request, current_app

from .. import db
from ..models import Comment, Blog_post, Admin, User
from . import admin
from ..decorators import admin_required
from ..user.forms import SearchForm
from .forms import NoticeForm


@admin.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now()
        db.session.add(current_user)
        db.session.commit()
    g.search_form = SearchForm()


@admin.route('/')
@admin_required
@login_required
def index():

    return render_template('admin/admin.html',
                           title='Home')

@admin.route('/admincomment/')
@admin_required
@login_required
def admin_comment():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    return render_template('admin/admin_comment.html',
                           comments=comments,
                           pagination=pagination,
                           page=page,
                           nums=len(comments),
                           title='Review')
@admin.route('/adminrecover/<int:id>')
@login_required
def admin_recover(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('admin.admin_comment'))

@admin.route('/admindelete/<int:id>')
@login_required
def admin_delete(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('admin.admin_comment'))

@admin.route('/adminpost/')
@admin_required
@login_required
def admin_post():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('admin/admin_post.html',posts=posts,pagination=pagination,page=page,nums = len(posts),title='Admin Post')

# blog post recovery
@admin.route('/recoverpost/<int:id>')
@login_required
def recover_post(id):
    post = Post.query.get_or_404(id)
    post.disabled = False
    db.session.add(post)
    return redirect(url_for('admin.admin_post'))

# deletion
@admin.route('/deletepost/<int:id>')
@login_required
def delate_post(id):
    post = Post.query.get_or_404(id)
    post.disabled = True
    db.session.add(post)
    return redirect(url_for('admin.admin_post'))

# Add notice
@admin.route('/notice', methods=['GET','POST'])
@login_required
@admin_required
def add_notice():
    notice = Admin.query.order_by(Admin.timestamp.desc()).first()
    if notice:
        db.session.delete(notice)
    form = NoticeForm()
    if form.validate_on_submit():
        admin = Admin(
            notice = form.body.data
        )
        db.session.add(admin)
        return redirect(url_for('admin.index'))
    return render_template('admin/admin_notice.html',title='site Announcement',form=form)

# get all users
@admin.route('/users')
@login_required
@admin_required
def admin_user():
    users = User.query.all()

    return render_template('admin/admin_user.html',title='all users',users=users)
