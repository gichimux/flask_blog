from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, abort, make_response, g, current_app
from flask_login import current_user, login_required

from .. import db
from . import user
from .forms import ProfileForm, PostForm, CommentForm, ReplyForm, SearchForm, EditpostForm
from ..models import User, Blog_post, Comment, Like, Permission, Admin
from ..decorators import permission_required


#user last visit time , text search
@user.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now()
        db.session.add(current_user)
        db.session.commit()
    g.search_form = SearchForm()

@user.route('/')
@user.route('/index')
def index():
    notice = Admin.query.order_by(Admin.timestamp.desc()).first()
    if notice:
        notice=notice.notice
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )

    posts = [post for post in pagination.items if post.draft==False]
    return render_template('user/index.html',
                           title = 'Home',
                           posts=posts,
                           notice=notice,
                           pagination=pagination)

@user.route('/user/<nickname>')
# @login_required
def users(nickname):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash(nickname + 'Not found')
        return redirect(url_for('user.index'))
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    posts = [post for post in posts if post.draft == False]
    return render_template('user/user.html',user=user,posts=posts,title='Information')

# edit user profile
@user.route('/edit_profile', methods=['GET','POST'])
@login_required
def edit_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.nickname = form.nickname.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Data successfully updated')
        return redirect(url_for('user.users',nickname=current_user.nickname))
    else:
        form.nickname.data = current_user.nickname
        form.about_me.data = current_user.about_me
    return render_template('user/editprofile.html',
                           form=form,
                           title='edit Infomation')

# write blog post
@user.route('/write', methods=['GET','POST'])
def write():
    form = PostForm()
    if current_user.operation(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        if 'save_draft' in request.form and form.validate():
            post = Post(body=form.body.data,
                        title=form.title.data,
                        draft= True,
                        author = current_user._get_current_object())
            db.session.add(post)
            flash('Saved successfully')
        elif 'submit' in request.form and form.validate():
            post = Post(body=form.body.data,
                        title=form.title.data,
                        author=current_user._get_current_object())
            db.session.add(post)
            flash('Post has been successfully Published')
        return redirect(url_for('user.write'))
    return render_template('user/write.html',
                           form=form,
                           post=form.body.data,
                           title='write a blog post')

# draft
@user.route('/draft/')
@login_required
def draft():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    drafts = [post for post in posts if post.draft==True]

    return render_template('user/draft.html',title='草稿',pagination=pagination,drafts=drafts)

# delete post draft
@user.route('/delete-draft/<int:id>')
@login_required
def delete_draft(id):
    draft = Post.query.get_or_404(id)
    draft.disabled = True
    db.session.add(draft)
    flash('Successfully Deleted')
    return redirect(url_for('user.draft'))


# article details
@user.route('/post/<int:id>', methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)
    post.view_num += 1
    db.session.add(post)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,post=post, unread=True,author=current_user._get_current_object())
        db.session.add(comment)
        flash('comment published')
        return redirect(url_for('user.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) / \
               current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False
    )
    comments = pagination.items
    return render_template('user/post.html', posts=[post],title=post.title, id=post.id,post=post, form=form,comments=comments,pagination=pagination)

# like
@user.route('/like/<int:id>')
@login_required
def like(id):
    post = Post.query.get_or_404(id)

    if post.like_num.filter_by(liker_id=current_user.id).first() is not None:
        flash('Already liked')
        return redirect(url_for('user.post', id=post.id))
    like = Like(post=post, unread=True,
                user=current_user._get_current_object())
    db.session.add(like)
    flash('Liked!')
    return redirect(url_for('user.post', id=post.id))

# unlike
@user.route('/unlike/<int:id>')
@login_required
def unlike(id):
    post = Post.query.get_or_404(id)
    if post.like_num.filter_by(liker_id=current_user.id).first() is None:
        flash('Not liked yet')
        return redirect(url_for('user.post', id=post.id))
    else:
        f = post.like_num.filter_by(liker_id=current_user.id).first()
        db.session.delete(f)
        flash('Unliked')
        return redirect(url_for('user.post', id=post.id))

#coment reply
@user.route('/reply/<int:id>', methods=['GET','POST'])
@login_required
def reply(id):
    comment = Comment.query.get_or_404(id)
    post = Post.query.get_or_404(comment.post_id)
    page = request.args.get('page', 1, type=int)
    form = ReplyForm()
    if form.validate_on_submit():
        reply_comment = Comment(body=form.body.data,
                                unread=True,
                                post=post,comment_type='reply',
                                reply_to=comment.author.nickname,
                                author=current_user._get_current_object())
        db.session.add(reply_comment)
        flash('Reply published')
        return redirect(url_for('user.post', id=comment.post_id, page=page))
    return render_template('user/reply.html',form=form,comment=comment,title='reply')

#recover
@user.route('/recover/<int:id>')
@login_required
def recover(id):
    comment = Comment.query.get_or_404(id)
    post_id = comment.post_id
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('user.post',id=post_id))

# delete
@user.route('/delete/<int:id>')
@login_required
def delate(id):
    comment = Comment.query.get_or_404(id)
    post_id = comment.post_id
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('user.post',id=post_id))

# edit article
@user.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
        not current_user.operation(Permission.ADMINISTER):
        abort(403)
    form = EditpostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        if post.draft == True:
            if 'save_draft' in request.form and form.validate():
                db.session.add(post)
                flash('Saved')
            elif 'submit' in request.form and form.validate():
                post.draft = False
                db.session.add(post)
                flash('Published!')
            return redirect(url_for('user.edit', id=post.id))
        else:
            db.session.add(post)
            flash('Post Updated')
            return redirect(url_for('user.post', id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    return render_template('user/editpost.html',
                           form=form,
                           post=post,
                           title='Edit Article')

# follow
@user.route('/follow/<nickname>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('无效的用户。')
        return redirect(url_for('user.index'))
    if current_user.is_following(user):
        flash('你已经关注了此用户。')
        return redirect(url_for('user.users', nickname=nickname))
    current_user.follow(user)
    flash('你已关注 %s。' % nickname)
    return redirect(url_for('user.users', nickname=nickname))

# 取消关注
@user.route('/unfollow/<nickname>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('无效的用户。')
        return redirect(url_for('user.index'))
    if not current_user.is_following(user):
        flash('你已经取消了此用户的关注。')
        return redirect(url_for('user.users', nickname=nickname))
    current_user.unfollow(user)
    flash('你已取消关注 %s 。' % nickname)
    return redirect(url_for('user.users', nickname=nickname))


@user.route('/follows/<nickname>')
@login_required
def follows(nickname):

    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('无效的用户。')
        return redirect(url_for('user.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    pagination2 = user.followed.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False
    )
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed',''))

    if show_followed:
        follows = [{'user': i.follower, 'timestamp': i.timestamp}
                   for i in pagination.items]
    else:
        follows = [{'user': i.followed, 'timestamp': i.timestamp}
                   for i in pagination2.items]

    return render_template('user/follow.html', user=user,
                           title='关注',
                           show_followed=show_followed,
                           pagination=pagination,
                           Permission=Permission,
                           follows=follows)
# 设置cookies
@user.route('/followers/<nickname>')
def show_follower(nickname):
    resp = make_response(redirect(url_for('user.follows',nickname=nickname)))
    resp.set_cookie('show_followed','1',max_age=30*24*60*60)
    return resp
@user.route('/followed/<nickname>')
def show_followed(nickname):
    resp = make_response(redirect(url_for('user.follows',nickname=nickname)))
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

# 全文搜索
@user.route('/search', methods=['GET','POST'])
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('user.index'))
    return redirect(url_for('user.search_results', query=g.search_form.search.data))
# 搜索结果
@user.route('/search_results/<query>')
def search_results(query):
    results = Post.query.whooshee_search(query).all()
    return render_template('user/search_results.html',
                           query=query,
                           title='搜索结果',
                           posts=results)
