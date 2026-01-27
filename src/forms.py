from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, BooleanField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
import re

class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    id_number = StringField('ID Number', validators=[DataRequired(), Length(min=13, max=13)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    rank = SelectField('Rank', choices=[
        ('constable', 'Constable'),
        ('sergeant', 'Sergeant'),
        ('captain', 'Captain'),
        ('major', 'Major'),
        ('colonel', 'Colonel')
    ])
    station = StringField('Station', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm Password')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class CaseForm(FlaskForm):
    title = StringField('Case Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('theft', 'Theft'),
        ('assault', 'Assault'),
        ('burglary', 'Burglary'),
        ('fraud', 'Fraud'),
        ('drugs', 'Drug Related'),
        ('homicide', 'Homicide'),  # ADDED THIS
        ('other', 'Other')
    ])
    severity = SelectField('Severity', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')  # ADDED THIS
    ])
    location = StringField('Location')
    # Changed to StringField to handle datetime-local input properly
    incident_date = StringField('Incident Date')

class SuspectForm(FlaskForm):
    id_number = StringField('ID Number', validators=[DataRequired(), Length(min=13, max=13)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    gender = SelectField('Gender', choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    address = TextAreaField('Address')
    contact_number = StringField('Contact Number')
    photo = FileField('Suspect Photo', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])

class SearchForm(FlaskForm):
    search_type = SelectField('Search Type', choices=[
        ('suspect', 'Suspect'),
        ('case', 'Case')
    ])
    query = StringField('Search Query', validators=[DataRequired()])