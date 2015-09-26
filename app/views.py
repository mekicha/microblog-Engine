from flask import render_template, flash, redirect, session, url_for, request, g
from app import app, db, lm, oid 
from flask.ext.login import login_user, logout_user, current_user, login_required
from .models import User, Post
from .forms import LoginForm, EditForm, PostForm, SearchForm, RegisterForm
from datetime import datetime
from config import POSTS_PER_PAGE
from .emails import follower_notification



@lm.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.before_request
def before_request():
	g.user = current_user
	if g.user.is_authenticated():
		g.user.last_seen = datetime.utcnow()
		db.session.add(g.user)
		db.session.commit()
		g.search_form = SearchForm()

@app.route('/', methods=['GET','POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET','POST'])
@login_required
def index(page=1):
	form = PostForm()
	if form.validate_on_submit():
		post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=g.user)
		db.session.add(post)
		db.session.commit()
		flash('Your post has been published!')
		return redirect(url_for('index'))
	posts = g.user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
	return render_template('index.html',
		    title='Home',
		    form=form,
		    posts=posts)


    
@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
	if g.user is not None and g.user.is_authenticated():
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		flash('Successfully logged in as %s' %form.email.data)
		session['remember_me'] = form.remember_me.data
		session['user_id'] = form.user.id
		return redirect(url_for('index'))	
	return render_template('login.html',
		                   title = 'Sign In',
		                   form = form)

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
	if form.validate_on_submit():
		user = User(form.username.data, form.email.data, form.password.data)
		db.session.add(user)
		db.session.commit()
		session['user_id'] = user.id
		flash('You are now Successfully registered')
		return redirect(url_for('index'))
	return render_template('register.html',
		                  form=form)


@app.route('/logout')
def logout():
	logout_user()
	form =LoginForm()
	return render_template('logout.html',
		                   form=form)


@app.route('/user/<username>')
@app.route('/user/<username>/<int:page>')
@login_required
def user(username, page=1):
	user = User.query.filter_by(username = username).first()
	if user == None:
		flash('User %s not found.' %username)
		return redirect(url_for('index'))
	posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
	return render_template('user.html',
		                   user = user,
		                   posts = posts)


@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
	form = EditForm(g.user.username)
	if form.validate_on_submit():
		g.user.username = form.username.data
		g.user.about_me = form.about_me.data
		db.session.add(g.user)
		db.session.commit()
		flash('Your changes have been saved.')
		return redirect(url_for('edit'))
	else:
		form.username.data = g.user.username
		form.about_me.data = g.user.about_me
	return render_template('edit.html', form = form)

@app.route('/follow/<username>')
@login_required
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('User %s not found.' % username)
		return redirect(url_for('index'))
	if user == g.user:
		flash('You can\'t follow yourself!')
		return redirect(url_for('user', username=username))
	u = g.user.follow(user)
	if u is None:
		flash('cannot follow' + username + '.')
		return redirect(url_for('user', username=username))
	db.session.add(u)
	db.session.commit()
	flash('You are now following ' + username + '!')
	follower_notification(user, g.user)
	return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('User %s not  found.' % username)
		return redirect(url_for('index'))
	if user == g.user:
		flash('You can\t unfollow yourself!')
		return redirect(url_for('user', username=username))
	u = g.user.unfollow(user)
	if u is None:
		flash('Cannot unfollow ' + username + '.')
		return redirect(url_for('user', username=username))
	db.session.add(u)
	db.session.commit()
	flash('You unfollowed ' + username + '.')
	return redirect(url_for('user', username=username))

@app.route('/search', methods=['POST'])
@login_required
def search():
	if not g.search_form.validate_on_submit():
		return redirect(url_for('index'))
	return redirect(url_for('search_results', query=g.search_form.search.data))

from config import MAX_SEARCH_RESULTS
@app.route('/search_results/<query>')
@login_required
def search_results(query):
	results = Post.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
	return render_template('search_results.html',
		                  query=query,
		                  results=results)

@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500




