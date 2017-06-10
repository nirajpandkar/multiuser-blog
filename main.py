#!/usr/bin/env python
import webapp2
import jinja2
import os
import re
import hmac
import datetime
import time
from google.appengine.ext import db

from models import Post, Comment, User

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


# Validation


def valid_username(username):
    return username and USER_RE.match(username)


def valid_password(password):
    return password and PASS_RE.match(password)


def valid_email(email):
    return not email or EMAIL_RE.match(email)

# Handlers


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

    def set_login_cookie(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def reset_cookie(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

# User authentication handlers


class SignUpHandler(BlogHandler):
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

        print "Params: " + str(params)
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
                self.set_login_cookie(u)    # Will have to be outside body
                # of else if anonymous users are allowed
                self.redirect("/welcome")


class LoginHandler(BlogHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")

        u = User.login(username, password)  # check whether username and
        # password are correct

        if u:
            self.set_login_cookie(u)
            self.redirect("/welcome")
        else:
            error_msg = "User doesn't exists or wrong password"  # Can be
            # fine tuned for precise errors
            self.render("login.html", error_username=error_msg)


class LogoutHandler(BlogHandler):
    def get(self):
        self.reset_cookie()
        self.redirect("/signup")


class MainHandler(BlogHandler):
    def get(self):
        self.render("base.html", username=self.user)


class MultiplePostHandler(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created DESC")
        if self.user:
            user = self.user
            logged_in_user = user.name
        else:
            logged_in_user = ""
        self.render("posts.html", posts=posts, username=self.user,
                    logged_in_user=logged_in_user)


class NewPostHandler(BlogHandler):
    def get(self):
        if self.read_secure_cookie("user_id"):
            self.render("newpost.html", username=self.user)
        else:
            self.redirect("/login")

    def post(self):
        subject = self.request.get("subject")
        body = self.request.get("body")

        if not body or not subject:
            error = "Subject and body can't be blank!"
            self.render("newpost.html", username=self.user, error=error,
                        subject=subject, body=body)
        else:
            user_id = self.read_secure_cookie("user_id").split("|")[0]
            username = User.by_id(int(user_id)).name
            author = username

            Post(subject=subject, body=body, author=author, liked_users=[]
                 ).put()
            time.sleep(0.1)
            self.redirect("/posts")


class EditPostHandler(BlogHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id))

        if self.read_secure_cookie("user_id"):
            self.render("edit.html", post=post)
        else:
            self.redirect("/login")

    def post(self, post_id):
        post = Post.get_by_id(int(post_id))
        new_subject = self.request.get("subject")
        new_body = self.request.get("body")

        if not new_body or not new_subject:
            post = Post.get_by_id(int(post_id))
            error = "Body and subject can't be blank!"
            self.render("edit.html", post=post, username=self.user,
                        error=error)
        else:
            post.subject = new_subject
            post.body = new_body
            post.last_edited = datetime.datetime.now()
            post.put()
            self.redirect("/posts/" + str(post_id))


class DeletePostHandler(BlogHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id))
        post.delete()
        time.sleep(0.1)
        self.redirect('/posts')


class NewCommentHandler(BlogHandler):
    def get(self, post_id):
        if self.read_secure_cookie("user_id"):
            post = Post.get_by_id(int(post_id))
            self.render("newcomment.html", post=post, username=self.user)
        else:
            self.redirect("/signup")

    def post(self, post_id):
        body = self.request.get("body")
        if not body:
            post = Post.get_by_id(int(post_id))
            error = "Comment can't be blank"
            self.render("newcomment.html", post=post, username=self.user,
                        error=error)
        else:
            user_id = self.read_secure_cookie("user_id").split("|")[0]
            author = User.by_id(int(user_id)).name

            Comment(body=body, author=author, post_id=int(post_id)).put()
            time.sleep(0.1)
            self.redirect("/posts/" + str(post_id))


class EditCommentHandler(BlogHandler):
    def get(self, comment_id):
        post_info = db.GqlQuery("SELECT * FROM Comment where __key__ = KEY("
                           "'Comment'," + comment_id + ")").fetch(1)
        for p in post_info:
            continue
        post = Post.get_by_id(int(p.post_id))
        comment = Comment.get_by_id(int(comment_id))
        time.sleep(0.1)
        self.render("editcomment.html", comment=comment, post=post)

    def post(self, comment_id):
        body = self.request.get("body")
        comment = Comment.get_by_id(int(comment_id))
        post = db.GqlQuery("SELECT * FROM Comment where __key__ = KEY("
                           "'Comment'," + comment_id + ")").fetch(1)

        comment.body = body
        comment.last_edited = datetime.datetime.now()
        comment.put()
        time.sleep(0.1)
        for p in post:
            continue
        self.redirect("/posts/" + str(p.post_id))


class DeleteCommentHandler(BlogHandler):
    def get(self, comment_id):
        posts = db.GqlQuery("SELECT * FROM Comment where __key__ = KEY("
                           "'Comment'," + comment_id + ")").fetch(1)
        comment = Comment.get_by_id(int(comment_id))
        comment.delete()
        time.sleep(0.1)    # trial and error, wasn't getting redirected
        # properly
        for p in posts:
            continue
        self.redirect("/posts/" + str(p.post_id))


class PermaLinkHandler(BlogHandler):
    def get(self, post_id):
        if self.user:
            user = self.user
            logged_in_user = user.name
        else:
            logged_in_user = ""
        post = Post.get_by_id(int(post_id))
        comments = db.GqlQuery("select * from Comment where post_id=" +
                               post_id).fetch(limit=None)
        self.render("permalink.html", post=post, username=self.user,
                    comments=comments, logged_in_user=logged_in_user)


class WelcomeHandler(BlogHandler):
    def get(self):
        if self.user:
            self.render("welcome.html", username=self.user)
        else:
            self.redirect("/signup")


class LikePostHandler(BlogHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id))
        user_id = self.user.key().id()

        print post.author + " " + self.user.name
        if post.author == self.user.name:
            return self.redirect("/posts/" + str(post_id))

        if user_id not in post.liked_users:
            post.liked_users.append(user_id)
        else:
            post.liked_users.remove(user_id)

        post.put()
        time.sleep(0.1)
        self.redirect("/posts/" + str(post_id))


app = webapp2.WSGIApplication([
    ('/', MultiplePostHandler),
    ('/posts', MultiplePostHandler),
    ('/posts/(\d+)', PermaLinkHandler),
    ('/newpost', NewPostHandler),
    ('/signup', SignUpHandler),
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/welcome', WelcomeHandler),
    ('/edit/(\d+)', EditPostHandler),
    ('/delete/(\d+)', DeletePostHandler),
    ('/newcomment/(\d+)', NewCommentHandler),
    ('/editcomment/(\d+)', EditCommentHandler),
    ('/deletecomment/(\d+)', DeleteCommentHandler),
    ('/likepost/(\d+)', LikePostHandler)
], debug=True)
