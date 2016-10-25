from google.appengine.ext import db


class Post(db.Model):
    subject = db.StringProperty()
    body = db.StringProperty()

