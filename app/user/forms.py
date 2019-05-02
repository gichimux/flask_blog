from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from flask_pagedown.fields import PageDownField


class ProfileForm(FlaskForm):
    nickname = StringField('nickname', validators=[Length(0, 7)])
    about_me = PageDownField('about me', validators=[Length(0, 140)])

class PostForm(FlaskForm):
    body = TextAreaField('Write a blog post', validators=[DataRequired()])
    title = StringField('title', validators=[Length(1, 20)])
    save_draft = SubmitField('save draft')
    submit = SubmitField('Submit')

class EditpostForm(FlaskForm):
    title = StringField('title', validators=[Length(1, 20)])
    body = TextAreaField('Edit Post', validators=[DataRequired()])
    update = SubmitField('update')
    submit = SubmitField('Submit')
    save_draft = SubmitField('save')

class CommentForm(FlaskForm):
    body = PageDownField('comment', validators=[DataRequired()])

# comment reply form
class ReplyForm(FlaskForm):
    body = PageDownField('Reply', validators=[DataRequired()])

# search form
class SearchForm(FlaskForm):
    search = StringField('search', validators=[DataRequired()])
