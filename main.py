import webapp2

from user import *
from post import *
from util import *


class BlogHandler(webapp2.RequestHandler):
    """Contains useful functions for all handlers"""
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template, **kw):
        self.write(render_str(template, **kw))

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


class FrontPage(BlogHandler):
    """Front page of the blog, displays 10 most recent posts"""
    def get(self):
        posts = Post.all().order("-created")
        self.render("front.html", posts=posts, user=self.user)


class SignUp(BlogHandler):
    """Sign up page where users can create an account"""
    def get(self):
        self.render("signup.html", user=self.user)

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")

        have_error = False
        params = dict(username=username, email=email)

        # check username
        if not is_valid_username(username):
            params["error_username"] = "This isn't a valid username."
            have_error = True
        elif User.by_name(username):
            params["error_username"] = "This username is taken."
            have_error = True

        # check password
        if not is_valid_password(password):
            params["error_password"] = "This isn't a valid password."
            have_error = True
        elif password != verify:
            params["error_verify"] = "Your passwords didn't match."
            have_error = True

        # check email
        if not is_valid_email(email):
            params["error_email"] = "This isn't a valid email."
            have_error = True

        if have_error:
            # there was an error, re-render signup.html with errors
            self.render("signup.html", **params)
        else:
            # there was no error, register user
            u = User.register(str(username), str(password), str(email))
            u.put()

            self.set_secure_cookie("username", u.username)
            self.redirect("/blog/welcome")


class Welcome(BlogHandler):
    """Welcome a newly created user, confirming account creation"""
    def get(self):
        username = self.read_secure_cookie("username")
        self.render("welcome.html", username=username)


class Login(BlogHandler):
    """Login page where users can login into their account"""
    def get(self):
        self.render("login.html", user=self.user)

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")

        # check if credentials are valid
        u = User.is_valid_login(str(username), str(password))
        if u:
            self.login(u)
            self.redirect("/")
        else:
            error = "Invalid login. Please try again."
            self.render("login.html", error=error, user=self.user)


class Logout(BlogHandler):
    """Logout user"""
    def get(self):
        self.logout()
        self.redirect("/blog/login")


class SinglePost(BlogHandler):
    """Displays a single blog post"""
    def get(self, post_id):
        post_key = db.Key.from_path("Post", int(post_id), parent=blog_key())
        post = db.get(post_key)

        if not post:
            # Post was not found
            self.render("404.html")
        else:
            self.render("permalink.html",
                        post=post,
                        liked=self.user and UserLike
                        .by_post_id_username(str(post_id),
                                             str(self.user.username)),
                        comments=Comment.by_post_id(str(post_id)),
                        user=self.user)


class NewPost(BlogHandler):
    """Form to create a new blog post"""
    def get(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            self.render("newpost.html", user=self.user)

    def post(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            subject = self.request.get("subject")
            content = self.request.get("content")

            if subject and content:
                # Ensure form was filled and the user is logged in
                p = Post(parent=blog_key(),
                         subject=subject,
                         content=content,
                         created_by=self.user.username)
                p.put()
                self.redirect("/blog/%s" % str(p.key().id()))
            else:
                # The form was not complete
                error = "Please include Subject and Content."
                self.render("newpost.html",
                            subject=subject,
                            content=content,
                            error=error,
                            user=self.user)


class DeletePost(BlogHandler):
    """Delete a blog post"""
    def get(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            post_id = self.request.get("post_id")
            post_key = db.Key.from_path("Post",
                                        int(post_id),
                                        parent=blog_key())
            post = db.get(post_key)

            if post.created_by == self.user.username:
                # The user did create the post, delete it
                post.delete()
                msg = "Your post has been successfully deleted."
                self.render('confirmation.html', msg=msg, user=self.user)
            else:
                # The user did NOT create the post, can't delete it
                msg = "You can't delete this post because\
                    you didn't create it."
                self.render("permalink.html",
                            post=post,
                            liked=self.user and UserLike
                            .by_post_id_username(str(post_id),
                                                 str(self.user.username)),
                            comments=Comment.by_post_id(str(post_id)),
                            error=msg,
                            user=self.user)


class EditPost(BlogHandler):
    """Form to edit a blog post"""
    def get(self):
        if not self.user:
            redirect("/blog/login")
        else:
            post_id = self.request.get("post_id")
            post_key = db.Key.from_path("Post",
                                        int(post_id),
                                        parent=blog_key())
            post = db.get(post_key)

            if post.created_by == self.user.username:
                # The user did create the post, edit it
                self.render("editpost.html",
                            post_id=post_id,
                            subject=post.subject,
                            content=post.content,
                            user=self.user)
            else:
                # The user did NOT create the post, can't edit it
                msg = "You can't edit this post because you\
                    didn't create it."
                self.render("permalink.html",
                            post=post,
                            liked=self.user and UserLike
                            .by_post_id_username(str(post_id),
                                                 str(self.user.username)),
                            comments=Comment.by_post_id(str(post_id)),
                            error=msg,
                            user=self.user)

    def post(self):
        if not self.user:
            redirect("/blog/login")
        else:
            subject = self.request.get("subject")
            content = self.request.get("content")
            post_id = self.request.get("post_id")

            post_key = db.Key.from_path("Post",
                                        int(post_id),
                                        parent=blog_key())
            post = db.get(post_key)

            if post.created_by == self.user.username:
                if subject and content:
                    post.subject = subject
                    post.content = content
                    post.put()
                    self.redirect("/blog/%s" % str(post_id))
                else:
                    # The form was not complete
                    msg = "Please include Subject and Content."
            else:
                # The user didn't create this post
                msg = "You can't edit this post because you didn't create it."
                self.render("editpost.html",
                            post_id=post_id,
                            subject=subject,
                            content=content,
                            error=msg,
                            user=self.user)


class LikePost(BlogHandler):
    """User can like a blog post"""
    def get(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            post_id = self.request.get("post_id")
            post_key = db.Key.from_path("Post",
                                        int(post_id),
                                        parent=blog_key())
            post = db.get(post_key)

            liked = False
            msg = ""

            if post.created_by == self.user.username:
                # The user created this post, can't like it
                msg = "You can't like your own post."
            else:
                like = UserLike.by_post_id_username(post_id,
                                                    self.user.username)
                # toggle like
                if like:
                    like.delete()
                    liked = False
                else:
                    like = UserLike(parent=likes_key(),
                                    post_id=post_id,
                                    username=self.user.username)
                    like.put()
                    liked = True

            self.render("permalink.html",
                        post=post,
                        liked=liked,
                        comments=Comment.by_post_id(str(post_id)),
                        error=msg,
                        user=self.user)


class NewComment(BlogHandler):
    """Form to create a comment for a blog post"""
    def get(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            post_id = self.request.get("post_id")
            post_key = db.Key.from_path("Post",
                                        int(post_id),
                                        parent=blog_key())
            post = db.get(post_key)

            self.render("newcomment.html", post=post, user=self.user)

    def post(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            comment = self.request.get("comment")
            post_id = self.request.get("post_id")

            if comment:
                c = Comment(parent=comments_key(),
                            content=comment,
                            post_id=post_id,
                            created_by=self.user.username)
                c.put()
                self.redirect("/blog/%s" % str(post_id))
            else:
                msg = "Please write a comment."
                self.render("newcomment.html",
                            post=post,
                            comment=comment,
                            error_comment=msg,
                            user=self.user)


class DeleteComment(BlogHandler):
    """Delete a comment"""
    def get(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            comment_id = self.request.get("comment_id")
            comment_key = db.Key.from_path("Comment",
                                           int(comment_id),
                                           parent=comments_key())
            comment = db.get(comment_key)

            post_id = comment.post_id
            post_key = db.Key.from_path("Post",
                                        int(post_id),
                                        parent=blog_key())
            post = db.get(post_key)

            if comment.created_by == self.user.username:
                comment.delete()
                msg = "Your comment has been successfully deleted."
            else:
                # The user did NOT create the post, can't delete it
                msg = "You can't delete that comment because\
                    you didn't create it."

            self.render("permalink.html",
                        post=post,
                        liked=self.user and UserLike
                        .by_post_id_username(str(post_id),
                                             str(self.user.username)),
                        comments=Comment.by_post_id(str(post_id)),
                        error=msg,
                        user=self.user)


class EditComment(BlogHandler):
    """Form to edit a comment"""
    def get(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            comment_id = self.request.get("comment_id")
            comment_key = db.Key.from_path("Comment",
                                           int(comment_id),
                                           parent=comments_key())
            comment = db.get(comment_key)

            post_id = comment.post_id
            post_key = db.Key.from_path("Post",
                                        int(post_id),
                                        parent=blog_key())
            post = db.get(post_key)

            if comment.created_by == self.user.username:
                # The user did create the comment, edit it
                self.render("newcomment.html",
                            post=post,
                            comment=comment.content,
                            user=self.user)
            else:
                # The user did NOT create the comment, can't edit it
                msg = "You can't edit that comment\
                    because you didn't create it."
                self.render("permalink.html",
                            post=post,
                            liked=self.user and UserLike
                            .by_post_id_username(str(post_id),
                                                 str(self.user.username)),
                            comments=Comment.by_post_id(str(post_id)),
                            error=msg,
                            user=self.user)

    def post(self):
        if not self.user:
            self.redirect("/blog/login")
        else:
            content = self.request.get("comment")
            comment_id = self.request.get("comment_id")
            comment_key = db.Key.from_path("Comment",
                                           int(comment_id),
                                           parent=comments_key())
            comment = db.get(comment_key)
            post_id = comment.post_id

            if comment.created_by == self.user.username:
                if comment:
                    comment.content = content
                    comment.put()
                    self.redirect("/blog/%s" % str(post_id))
                    return
                else:
                    # No comment was written
                    msg = "Please write a comment."
            else:
                # The user didn't create this comment
                msg = "You can't edit that comment\
                    because you didn't create it."

            post_key = db.Key.from_path("Post",
                                        int(post_id),
                                        parent=blog_key())
            post = db.get(post_key)
            self.render("newcomment.html",
                        post=post,
                        comment=comment,
                        error_comment=msg,
                        user=self.user)

app = webapp2.WSGIApplication([("/", FrontPage),
                               ("/blog/signup", SignUp),
                               ("/blog/welcome", Welcome),
                               ("/blog/login", Login),
                               ("/blog/logout", Logout),
                               ("/blog/([0-9]+)", SinglePost),
                               ("/blog/newpost", NewPost),
                               ("/blog/delete", DeletePost),
                               ("/blog/edit", EditPost),
                               ("/blog/like", LikePost),
                               ("/blog/newcomment", NewComment),
                               ("/blog/comment/delete", DeleteComment),
                               ("/blog/comment/edit", EditComment)],
                              debug=True)
