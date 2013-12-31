from flask import Flask, request, url_for, redirect, g, session, flash, abort, render_template, make_response
from forms import LoginForm , SignupForm
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY']= 'dsdsaxasdcdvsfcahuf286r783h782tg62367dggdb2387'

if os.environ.get('DATABASE_URL') is None:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///paste.db"
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

db = SQLAlchemy(app)

#-----------------------------------------------------------------------------------------------#
#                                                Models                                         #
#-----------------------------------------------------------------------------------------------#

class Comment(db.Model): 
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parent_paste = db.Column(db.Integer, db.ForeignKey('paste.id'))

    def __init__(self,message,user,paste):
        self.message = message
        self.pub_date = datetime.utcnow()
        self.user = user
        self.paste = paste 

    def __repr__(self):
        return '<Comment %r>' % self.id


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    password = db.Column(db.String(120))
    email = db.Column(db.String(240))
    pastes = db.relationship('Paste', lazy='dynamic', backref='user')
    comments = db.relationship('Comment', lazy='dynamic', backref='user', cascade="all, delete-orphan")

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.set_password(password)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
       
    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User %r>' % self.name


class Paste(db.Model):
    __tablename__ = 'paste'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    code = db.Column(db.Text)
    anonymous = db.Column(db.Boolean, unique=False, default=False)
    pub_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', lazy='dynamic', cascade="all, delete-orphan", backref='paste')

    def __init__(self, user, title, code,anonymous = False):
        self.user = user
        self.title = title
        self.anonymous = anonymous
        self.code = code
        self.pub_date = datetime.utcnow()

    def __repr__(self):
        return '<Paste %r>' % self.id


#-----------------------------------------------------------------------------------------------#
#                                            Before Request                                     #
#-----------------------------------------------------------------------------------------------#

@app.before_request
def check_user_status():
    g.user = None
    if 'user_email' in session:
        g.user = User.query.filter_by(email = session['user_email']).first()
    else:
        session['user_email'] = None
        session['user_name'] = None

#-----------------------------------------------------------------------------------------------#
#                                                Routes                                         #
#-----------------------------------------------------------------------------------------------#

@app.route('/', methods=('GET', 'POST'))
def home():
    reply_to = None
    parent = None
    reply_to_title=''
    if session['user_name']:
        user = User.query.filter_by(name = session['user_name']).first()
        if user.pastes.all():
            recent_paste = user.pastes.all()[-1].id
        else:
            recent_paste = None
    else:
        recent_paste = None
    if request.method == 'POST' and request.form['code']:
    	visibility = True
    	if request.form['visibility'] == "secret":
    		visibility = False
        title = None
        if request.form['title']:
            title = request.form['title']
        paste = Paste(g.user,title,request.form['code'],visibility)
        db.session.add(paste)
        db.session.commit()
        return redirect(url_for('show_paste', paste_id=paste.id))
    elif request.method == 'POST':
    	flash('You need to fill in the code field')
    if request.method == 'GET' and request.args.get('reply_to'):
        reply_id = request.args.get('reply_to')
        paste = Paste.query.filter_by(id = reply_id).first()
        if paste is not None:
            reply_to_title = "Reply to #%s"%(paste.id)
            return render_template('home.html', parent=parent, recent_paste=recent_paste,reply_to = paste,reply_to_title=reply_to_title)    
    return render_template('home.html', parent=parent, recent_paste=recent_paste,reply_to=reply_to,reply_to_title=reply_to_title)

@app.route('/<paste_id>',methods=('GET','POST'))
def show_paste(paste_id):
    if request.method == 'POST' and request.form['comment'] and session['user_name']:
        paste = Paste.query.filter_by(id = paste_id).first()
        user = User.query.filter_by(name = session['user_name']).first()
        comment = Comment(request.form['comment'],user,paste)
        db.session.add(comment)
        db.session.commit()
        flash('comment was successful')
        if paste:
            return render_template('show_paste.html', paste = paste)
        else:
            flash('You tried to post comment on a paste which is not available')
            return redirect(request.referrer or url_for())
    elif request.method == 'POST' and request.form['comment']:
        flash('In order to comment you need to be logged in!')
        return render_template('show_paste.html', paste = paste)
    paste = Paste.query.filter_by(id = paste_id).first()
    if paste: 
        return render_template('show_paste.html', paste = paste)
    else:
        abort(404)

@app.route('/<paste_id>/raw')
def view_raw(paste_id):
    response = make_response(Paste.query.filter_by(id = paste_id).first().code)
    response.headers["content-type"] = "text/plain"
    return response

@app.route('/<paste_id>/delete', methods=['GET', 'POST'])
def delete_paste(paste_id):
    paste = Paste.query.get(paste_id)
    if paste.user:
        if session['user_name'] is None or session['user_name'] != paste.user.name:
            abort(401)
    if request.method == 'POST':
        if 'yes' in request.form:
            comments = paste.user.comments.filter_by(parent_paste = 1).all()
            db.session.delete(paste)
            db.session.commit()
            flash('Paste was successfully deleted')
            return redirect(url_for('home'))
        else:
            return redirect(url_for('show_paste', paste_id=paste.id))
    return render_template('delete_paste.html', paste=paste)

@app.route('/my_pastes', methods=('GET', 'POST'))
def my_pastes():
    if request.method == 'GET':
        if session['user_email'] and session['user_name']:
            user_pastes = User.query.filter_by(name = session['user_name']).first().pastes.all()
            user_comments = User.query.filter_by(name = session['user_name']).first().comments.all()
            return render_template('my_pastes.html',pastes = user_pastes,comments = user_comments)
        else:
            flash('In order to view your pastes you need to be logged in!')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')
#---------------------------------------------Authentication------------------------------------#                                    

@app.route('/login', methods=('GET', 'POST'))
def login():
    if session['user_email']:
        flash('you are already logged in')
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.check_password(form.password.data):
            session['user_email'] = form.email.data
            session['user_name'] = user.name
            flash('Thanks for logging in')
            return redirect(url_for('home'))
        else:
            flash('Sorry! no user exists with this email and password')
            return render_template('login.html', form=form)
    return render_template('login.html', form=form)

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if session['user_email']:
        flash('you are already signed up')
        return redirect(url_for('home'))
    form = SignupForm()
    if form.validate_on_submit():
        print "nothins"
        user_name = User.query.filter_by(name=form.name.data).first()
        user_email = User.query.filter_by(email=form.email.data).first()
        if user_name is None and user_email is None:
            user = User(form.name.data,form.email.data,form.password.data)
            db.session.add(user)
            db.session.commit()
            session['user_email'] = form.email.data
            session['user_name'] = form.name.data
            flash('Thanks for registering. You are now logged in!')
            return redirect(url_for('home'))
        elif user_name is None:
            flash("email already exists. Choose another one!",'error')
            render_template('signup.html', form=form)
        else:
            flash("username already exists. Choose another one!",'error')
            render_template('signup.html', form=form)
    return render_template('signup.html', form=form)

@app.route('/logout', methods=('GET', 'POST'))
def logout():
    session.pop('user_email', None)
    session.pop('user_name', None)
    flash("You were successfully logged out")
    return redirect(request.referrer or url_for('home'))

#-----------------------------------------------------------------------------------------------#
#                                                Main run                                       #
#-----------------------------------------------------------------------------------------------#

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
