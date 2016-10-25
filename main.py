#!/usr/bin/env python
import webapp2
import jinja2
import os
from google.appengine.ext import db

from models import Post

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)



class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


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

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/posts', MultiplePostHandler),
    ('/posts/(\d+)', PermaLinkHandler),
    ('/newpost', NewPostHandler)
], debug=True)
