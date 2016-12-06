#!/usr/bin/env python
import webapp2
import jinja2
import os
import re
import hmac
import random
import string
import hashlib
from google.appengine.ext import db

from models import Post

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")

SECRET = "1497d98baea787eb6a8a676145c44212"

# Hashing, Salting
def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(SECRET, val).hexdigest())


def check_secure_val(val):
    original = val.split("|")[0]
    if make_secure_val(original) == val:
        return original


def make_salt(length=5):
    return "".join(random.choice(string.letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt)
    return "%s|%s" % (salt, h)


def valid_pw(name, pw, h):
    salt = h.split("|")[0]
    return make_pw_hash(name, pw, salt) == h
# Validation

def valid_username(username):
    return username and USER_RE.match(username)


def valid_password(password):
    return password and PASS_RE.match(password)


def valid_email(email):
    return not email or EMAIL_RE.match(email)


class BlogHandler(webapp2.RequestHandler):
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
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val)
        )

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')


class MainHandler(BlogHandler):
    def get(self):
        self.render("base.html")


class MultiplePostHandler(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created DESC")
        self.render("posts.html", posts=posts)


class NewPostHandler(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        body = self.request.get("body")

        Post(subject=subject, body=body).put()
        self.redirect("/posts")


class PermaLinkHandler(BlogHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id))
        self.render("permalink.html", post=post)

# Authentication Handlers


class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)

    @classmethod
    def by_name(cls, name):
        return User.all().filter('name =', name).get()

    @classmethod
    def register(cls, name, pw, email=None):
        password_hash = make_pw_hash(name, pw)
        return User(name=name,
                    pw_hash=password_hash,
                    email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


class SignUpHandler(BlogHandler):
    username = "niraj"
    password = "super"

    def get(self):
        self.render("signup.html")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        verify_password = self.request.get("verify_password")
        email = self.request.get("email")

        have_error = False

        params = dict(username=username, email=email)

        if not valid_username(username):
            params['error_username'] = "Invalid username"
            have_error = True

        if not valid_password(password):
            params['error_password'] = "Invalid password"
            have_error = True
        elif password != verify_password:
            params['error_verify_password'] = "Passwords do not match"
            have_error = True

        if not valid_email(email):
            params['error_email'] = "Invalid email"
            have_error = True

        if have_error:
            self.render("signup.html", **params)
        else:
            u = User.by_name(username)
            if u:
                error_msg = "This user already exists"
                self.render("signup.html", error_username=error_msg)
            else:
                u = User.register(username, password, email)
                u.put()
                self.login(u)
                self.redirect("/welcome")


class WelcomeHandler(BlogHandler):
    def get(self):
        if self.read_secure_cookie("user_id"):
            user_id = self.read_secure_cookie("user_id").split("|")[0]
            user = User.by_id(int(user_id))
            if user:
                self.render("welcome.html", username=user.name)
            else:
                self.redirect("/signup")
        else:
            self.redirect("/signup")


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/posts', MultiplePostHandler),
    ('/posts/(\d+)', PermaLinkHandler),
    ('/newpost', NewPostHandler),
    ('/signup', SignUpHandler),
    ('/welcome', WelcomeHandler)
], debug=True)
