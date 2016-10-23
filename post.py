from util import render_str

from google.appengine.ext import db


class Post(db.Model):
    """Data model for blog posts

    Attributes:
        required:
        subject (string): The blog post's title
        content (text): The blog post's content
        created (date): The date the post was created
        last_modified (date): The date the post was last modified
        created_by (string): The username of the creator
    """
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    created_by = db.StringProperty(required=True)

    def render(self):
        """Renders Post entity using a Jinja HTML template

        Return:
            The HTML template populated with the Post's data
        """
        self._render_text = self.content.replace("\n", "<br>")
        return render_str("post.html", p=self)


def blog_key(name="default"):
    """Groups Post entities under parent, "default"

    Args:
        group (string): The parent

    Returns:
        The key for data model Post
    """
    return db.Key.from_path("blogs", name)


class UserLike(db.Model):
    """Data model for a User's Like

    Attributes:
        required:
        post_id (string): The blog post's ID
        username (text): The user's username
    """
    post_id = db.StringProperty(required=True)
    username = db.StringProperty(required=True)

    @classmethod
    def by_post_id_username(cls, post_id, username):
        """Get UserLike entity by post_id and username

        Args:
            post_id (string): The post's ID
            username (string): The user's username

        Returns:
            The UserLike entity with the given username and post ID
        """
        return cls.all().filter("post_id =", post_id)\
            .filter("username =", username).get()


def likes_key(group="default"):
    """Groups UserLike entities under parent, "default"

    Args:
        group (string): The parent

    Returns:
        The key for data model UserLike
    """
    return db.Key.from_path("likes", group)


class Comment(db.Model):
    """Data model for blog comments

    Attributes:
        required:
        content (text): The blog post's content
        post_id (string): The blog post's ID
        created_by (string): The username of the creator
        created (date): The date the post was created
        last_modified (date): The date the post was last modified
    """
    content = db.TextProperty(required=True)
    post_id = db.StringProperty(required=True)
    created_by = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self, user):
        """Renders Comment entity using a Jinja HTML template

        Return:
            The HTML template populated with the Comment's data
        """
        self._render_text = self.content.replace("\n", "<br>")
        return render_str("comment.html", comment=self, user=user)

    @classmethod
    def by_post_id(cls, post_id):
        """Get comments by post ID

        Args:
            post_id (string): The blog post's ID

        Return:
            The comments from the post with the given ID
        """
        return cls.all().filter("post_id =", str(post_id))


def comments_key(group="default"):
    """Groups Comment entities under parent, "default"

    Args:
        group (string): The parent

    Returns:
        The key for data model Comment
    """
    return db.Key.from_path("comments", group)
