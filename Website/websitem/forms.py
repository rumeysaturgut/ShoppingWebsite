from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField,IntegerField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError,Optional
from websitem.models import User
from datetime import date


#kayıt olma formu
class RegistrationForm(FlaskForm):
    username = StringField('Kullanıcı Adı',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Parola', validators=[DataRequired()])
    confirm_password = PasswordField('Parolayı Doğrula',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Kaydol')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Bu kullanıcı adı kullanılmaktadır. Lütfen başka bir kullanıcı adı giriniz.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Bu e-posta kullanılmaktadır. Lütfen başka bir e-posta giriniz.')

#kullanıcı giriş formu
class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Beni Hatırla')
    submit = SubmitField('Giriş Yap')

#kullanıcı hesabı formu
class UpdateAccountForm(FlaskForm):
    username = StringField('Kullanıcı Adı',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Profil Resmini Güncelle', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Güncelle')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Bu kullanıcı adı kullanılmaktadır. Lütfen başka bir kullanıcı adı giriniz.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Bu e-posta kullanılmaktadır. Lütfen başka bir e-posta giriniz.')

#ürün formu
class ProductForm(FlaskForm):
    title = StringField('Ürün İsmi', validators=[DataRequired()])
    price = IntegerField('Fiyat',validators=[DataRequired()])
    category = SelectField('Kategori',choices=[('1','Elektronik'),('2','Ev-Ofis'),('3','Kozmetik'),('4','Giyim')],validators=[DataRequired()])
    picture = FileField('Ürün Resmi', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Ekle')

#kategoriye  ve tarih aralığına göre filterleme formu
class CategoryForm(FlaskForm):
    category = SelectField('Kategori',choices=[('0', 'Hepsi'),('1', 'Elektronik'), ('2', 'Ev-Ofis'), ('3', 'Kozmetik'), ('4', 'Giyim')],default='0')
    start_date = DateField('Başlangıç Tarih', format='%Y-%m-%d', validators=[Optional(strip_whitespace=True)])
    end_date = DateField('Bitiş Tarih', format='%Y-%m-%d', default=date.today(),validators=[Optional(strip_whitespace=True)])

    submit = SubmitField('Uygula')



