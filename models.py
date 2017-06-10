from google.appengine.ext import db
import hashlib
import random
import string


class Post(db.Model):
    subject = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.StringProperty()
    last_edited = db.DateTimeProperty(auto_now_add=True)
    liked_users = db.ListProperty(int)

    def number_likes(self):
        number_likes = len(self.liked_users)
        return number_likes


class Comment(db.Model):
    body = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.StringProperty()
    last_edited = db.DateTimeProperty(auto_now_add=True)
    user_id = db.IntegerProperty()
    post_id = db.IntegerProperty()


def make_salt(length=5):
    return "".join(random.choice(string.letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return "%s|%s" % (salt, h)


def valid_pw_hash(name, pw, h):
    salt = h.split("|")[0]
    return make_pw_hash(name, pw, salt) == h


class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)  # Replace User with cls for reusing
        # modules

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
        u = User.by_name(name)
        if u and valid_pw_hash(name, pw, u.pw_hash):
            return u

