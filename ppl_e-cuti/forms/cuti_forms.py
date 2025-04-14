from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from app.models.user import CutiType
from datetime import datetime

class CutiRequestForm(FlaskForm):
    cuti_type = SelectField('Jenis Cuti', choices=[(cuti.value, cuti.value.capitalize()) for cuti in CutiType])
    start_date = DateField('Tanggal Mulai', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('Tanggal Selesai', validators=[DataRequired()], format='%Y-%m-%d')
    reason = TextAreaField('Alasan', validators=[DataRequired()])
    attachment = FileField('Lampiran (Opsional)', 
                         validators=[FileAllowed(['pdf', 'jpg', 'png', 'jpeg', 'doc', 'docx'])])
    submit = SubmitField('Ajukan Cuti')
    
    def validate_end_date(self, end_date):
        if end_date.data < self.start_date.data:
            raise ValidationError('Tanggal selesai harus setelah tanggal mulai')
        
    def validate_start_date(self, start_date):
        if start_date.data < datetime.now().date():
            raise ValidationError('Tanggal mulai tidak boleh di masa lalu')

class CutiApprovalForm(FlaskForm):
    approval_notes = TextAreaField('Catatan', validators=[DataRequired()])
    submit_approve = SubmitField('Setujui')
    submit_reject = SubmitField('Tolak')