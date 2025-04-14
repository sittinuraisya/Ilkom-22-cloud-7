from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, BooleanField
from wtforms.validators import DataRequired

class HolidayForm(FlaskForm):
    name = StringField('Nama Hari Libur', validators=[DataRequired()])
    date = DateField('Tanggal', validators=[DataRequired()], format='%Y-%m-%d')
    is_recurring = BooleanField('Berulang Setiap Tahun')
    submit = SubmitField('Simpan')
