import os
import jinja2
import webapp2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "html")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

class MainPage(Handler):
    def get(self):
        self.render("base.html")

class NewPostHandler(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            p = Post(parent = blog_key(), subject=subject, content=content)
            p.put()
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

app = webapp2.WSGIApplication([
    ("/blog/?", MainPage),
    ("/blog/newpost", NewPostHandler),
    ("/blog/([0-9]+)", PostPageHandler)
], debug=True)
