from google.appengine.ext import db


class Post(db.Model):
    subject = db.StringProperty(required=True)
    body = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.StringProperty()
    last_edited = db.DateTimeProperty(auto_now_add=True)

