from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, URL, NumberRange

class ConfigForm(FlaskForm):
    url = StringField('M3U URL', validators=[DataRequired(), URL()])
    output = StringField('Output File Name', validators=[DataRequired()])
    maxage = IntegerField('Max Age Before Download (hours)', validators=[DataRequired(), NumberRange(min=1, max=24)])
    new_group_title = StringField('Custom Group Title')
    movies_dir = StringField('Movies Directory')
    series_dir = StringField('Series Directory')
    scan_interval = IntegerField('VOD Schedule Interval (hours)', validators=[DataRequired(), NumberRange(min=1, max=24)])
    enable_scheduler = SelectField('Enable VOD scheduler', choices=[('1', 'Yes'), ('0', 'No')], validators=[DataRequired()])
    overwrite_series = SelectField('Overwrite existing episodes', choices=[('1', 'Yes'), ('0', 'No')], validators=[DataRequired()])
    overwrite_movies = SelectField ('Overwrite existing movies', choices=[('1', 'Yes'), ('0', 'No')], validators=[DataRequired()])
    hide_webserver_logs = SelectField('Hide webserver logs', choices=[('1', 'Yes'), ('0', 'No')], validators=[DataRequired()])
    submit = SubmitField('Save')

