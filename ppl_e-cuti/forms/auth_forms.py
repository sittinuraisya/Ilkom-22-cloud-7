# app/forms/auth_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models.user import User, UserRole

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ingat Saya')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Nama Depan', validators=[DataRequired()])
    last_name = StringField('Nama Belakang', validators=[DataRequired()])
    department = StringField('Departemen', validators=[DataRequired()])
    position = StringField('Jabatan', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Konfirmasi Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Daftar')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username sudah digunakan. Silakan pilih username lain.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email sudah terdaftar. Silakan gunakan email lain.')

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Nama Depan', validators=[DataRequired()])
    last_name = StringField('Nama Belakang', validators=[DataRequired()])
    department = StringField('Departemen', validators=[DataRequired()])
    position = StringField('Jabatan', validators=[DataRequired()])
    role = SelectField('Role', choices=[(role.value, role.value.capitalize()) for role in UserRole 
                                        if role != UserRole.SUPERADMIN])
    atasan = SelectField('Atasan Langsung', coerce=int)
    password = PasswordField('Password Sementara', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Konfirmasi Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    force_change_password = BooleanField('Paksa Ganti Password', default=True)
    sisa_cuti = StringField('Sisa Cuti Tahunan', default=12)
    submit = SubmitField('Buat Akun')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username sudah digunakan.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email sudah terdaftar.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Password Saat Ini', validators=[DataRequired()])
    new_password = PasswordField('Password Baru', validators=[DataRequired(), Length(min=8)])
    confirm_new_password = PasswordField('Konfirmasi Password Baru', 
                                        validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Ubah Password')