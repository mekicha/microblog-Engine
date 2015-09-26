from flask.ext.wtf import Form 
from wtforms import StringField, BooleanField, TextAreaField, TextField, PasswordField
from wtforms.validators import DataRequired, Length
from app.models import User

class LoginForm(Form):
	email = TextField('Email', validators = [DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('remember_me', default = False)

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.user = None

	def validate(self):
		if not Form.validate(self):
			return False
		user = User.query.filter_by(email=self.email.data.lower()).first()

		if user is None:
			self.email.errors.append('Unknown email')
			return False

		if not user.check_password(self.password.data):
			self.password.errors.append('Invalid Password')
			return False

		self.user = user
		return True


class RegisterForm(Form):
	username = StringField('username', validators = [DataRequired()])
	email = TextField('Email', validators = [DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])

	def __init__(self, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		#self.user = None

	def validate(self):
		if not Form.validate(self):
			return False
		email_exists = User.query.filter_by(email=self.email.data).first()
		if email_exists:
			self.email.errors.append('Email already in use!')
			return False
		else:
			return True
       
       



class EditForm(Form):
	username = StringField('username', validators = [DataRequired()])
	about_me = TextAreaField('about_me', validators = [Length(min=0, max=140)])
	

	def __init__(self, original_username, *args, **kwargs):
		Form.__init__(self, *args, **kwargs)
		self.original_username = original_username

	def validate(self):
		if not Form.validate(self):
			return False
		if self.username.data == self.original_username:
			return True
		user = User.query.filter_by(username=self.user.data).first()
		if user != None:
			self.username.errors.append(' username already in use. Pick another one')
			return False
		return True

class PostForm(Form):
	post = StringField('post', validators=[DataRequired()])

class SearchForm(Form):
	search = StringField('search', validators=[DataRequired])
	
	
		