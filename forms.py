from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('立即注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被使用。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('该邮箱已被注册。')

class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('登录')

class ProductForm(FlaskForm):
    name = StringField('商品名称', validators=[DataRequired()])
    price = FloatField('价格 (元)', validators=[DataRequired()])
    image = FileField('商品图片', validators=[FileAllowed(['jpg', 'png'], '只支持图片文件!')])
    description = TextAreaField('商品描述', validators=[DataRequired()])
    submit = SubmitField('发布商品')

class CommentForm(FlaskForm):
    content = TextAreaField('发表评论', validators=[DataRequired(), Length(min=1, max=200)])
    submit = SubmitField('提交')