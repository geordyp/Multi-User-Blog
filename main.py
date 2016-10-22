import os
import re
import string
import random
import jinja2
import webapp2
import hashlib
import hmac

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "html")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

secret = 'iliketurtles'

#########################
# user sign up validation
#########################
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

def usernameIsTaken(username):
    users = db.GqlQuery("SELECT * FROM User")
    for u in users:
        if u.username == username:
            return True
    return False

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class User(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.StringProperty(required = False)

    @classmethod
    def by_id(cls, uid):
        return cls.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = cls.all().filter('username =', name).get()
        return u

    @classmethod
    def register(cls, username, password, email = None):
        pw_hash = make_pw_hash(username, password)
        return cls(parent = users_key(),
                    username = username,
                    password = pw_hash,
                    email = email)

    @classmethod
    def login(cls, username, password):
        u = cls.by_name(username)
        if u and valid_pw(username, password, u.password):
            return u

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    created_by = db.ReferenceProperty(User, required = False, collection_name = "posts")

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return self.render_str("post.html", p = self)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class Like(db.Model):
    post = db.ReferenceProperty(Post, required = True, collection_name = "likes")
    user = db.ReferenceProperty(User, required = True, collection_name = "likes")

#########################
# password hashing
#########################
def make_salt(length = 5):
    return ''.join(random.choice(string.letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()

    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(",")[1]
    return h == make_pw_hash(name, pw, salt)

#########################
# cookies
#########################
def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split("|")[0]
    if secure_val == make_secure_val(val):
        return val

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            "Set-Cookie",
            "%s=%s; Path=/" % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie("user_id")
        self.user = uid and User.by_id(int(uid))

class MainPage(Handler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render("front.html", posts=posts)

class PostPageHandler(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        # likes = post.likes.get()
        # num = 0
        # userLike = False
        # if likes:
        #     for like in likes:
        #         num = num + 1
        #         if like.user == self.user:
        #             userLike = True

        # self.render("permalink.html", post=post, post_id=post_id, userLike=userLike, num=num)
        self.render("permalink.html", post=post, post_id=post_id)

class NewPostHandler(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            p = Post(parent = blog_key(), subject=subject, content=content, created_by=self.user)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

class UserLoginHandler(Handler):
    def get(self):
        self.render("login.html")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")

        u = User.login(str(username), str(password))
        if u:
            self.login(u)
            self.redirect('/blog/welcome')
        else:
            error = "Invalid login"
            self.render("login.html", error=error)

class UserSignUpHandler(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        params = dict(username = username, email = email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True
        elif usernameIsTaken(username):
            params['error_username'] = "This user name is taken."
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup.html', **params)
        else:
            u = User.register(str(username), str(password), str(email))
            u.put()

            self.set_secure_cookie("username", u.username)
            self.redirect("/blog/welcome")

class LogoutHandler(Handler):
    def get(self):
        self.logout()
        self.redirect('/blog/signup')

class WelcomeHandler(Handler):
    def get(self):
        u_id = self.read_secure_cookie("user_id")
        if u_id:
            user = User.by_id(int(u_id))
            if user and valid_username(str(user.username)):
                self.render("welcome.html", username = str(user.username))
            else:
                self.redirect("/blog")
        else:
            name = self.read_secure_cookie("username")
            self.render("welcome.html", username = str(name))

class LikeHandler(Handler):
    def get(self):
        post_id = self.request.get("post_id")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if post.created_by == self.user:
            # TODO error message: can't like this post
            True
        else:
            likes = post.likes.get()
            userHasLiked = False
            # if likes:
            #     for like in likes:
            #         if like.user == self.user:
            #             # this user has already liked this post, so unlike
            #             like.key.delete()
            #             userHasLiked = True
            #     if (userHasLiked == False):
            #         l = Like(post=post, user=self.user)
            #         l.put()
            # else:
            l = Like(post=post, user=self.user)
            l.put()

        self.redirect("/blog/%s" % str(post_id))

class DeleteHandler(Handler):
    def get(self):
        post_id = self.request.get("post_id")
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        post.delete()

        msg = "Your post has been successfully deleted."
        self.render('confirmation.html', msg=msg)

app = webapp2.WSGIApplication([
    ("/blog/?", MainPage),
    ("/blog/newpost", NewPostHandler),
    ("/blog/([0-9]+)", PostPageHandler),
    ("/blog/signup", UserSignUpHandler),
    ("/blog/login", UserLoginHandler),
    ("/blog/welcome", WelcomeHandler),
    ("/blog/logout", LogoutHandler),
    ("/blog/like", LikeHandler),
    ("/blog/delete", DeleteHandler)
], debug=True)
