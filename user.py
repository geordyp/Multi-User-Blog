import string
import random
import hashlib
import re

from google.appengine.ext import db

class User(db.Model):
    """Data model for user

    Attributes:
        required:
        username (string): User's name
        pw_hash (string): User's hashed password

        optional:
        email (string): User's email address
    """
    username = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty(required=False)

    @classmethod
    def by_id(cls, uid):
        """Get User entity by ID

        Args:
            uid (integer): The user's ID

        Returns:
            The user entity with the given ID
        """
        return cls.get_by_id(uid, parent=users_key())

    @classmethod
    def by_name(cls, username):
        """Get User entity by name

        Args:
            username (string): The user's username

        Returns:
            The user entity with the given username
        """
        return cls.all().filter("username =", username).get()

    @classmethod
    def register(cls, username, pw, email=None):
        """Hashes the password and creates a User entity

        Args:
            username (string): User's username
            pw (string): User's password
            email (string): User's email

        Returns:
            A User entity
        """
        pw_hash = make_pw_hash(username, pw)
        return cls(parent=users_key(),
                   username=username,
                   pw_hash=pw_hash,
                   email=email)

    @classmethod
    def is_valid_login(cls, username, pw):
        """Check if user's username and password are valid

        Args:
            username (string): User's username
            pw (string): User's password

        Returns:
            The corresponding user entity if valid
        """
        u = cls.by_name(username)
        if u and is_valid_pw_login(username, pw, u.pw_hash):
            return u

def users_key(group="default"):
    """Groups User entities under parent, "default"

    Args:
        group (string): The parent

    Returns:
        The key for data model User
    """
    return db.Key.from_path("users", group)

def make_salt(length=5):
    """Creates a salt for password hashing

    Args:
        length (integer): The length of the salt

    Returns:
        The salt of the given length
    """
    return "".join(random.choice(string.letters) for x in xrange(length))

def make_pw_hash(name, pw, salt=None):
    """Creates a password hash

    Args:
        name (string): The user's name
        pw (string): The password
        salt (string): The password hash salt

    Returns:
        The password hash
    """
    if not salt:
        # don't create a new salt if one already exists
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return "%s,%s" % (h, salt)

def is_valid_pw_login(name, pw, h):
    """Checks if the given password is valid for login

    Args:
        name (string): The user's name
        pw (string): The password
        h (string): The password hash

    Returns:
        The True if the password is valid
    """
    salt = h.split(",")[1]
    return h == make_pw_hash(name, pw, salt)

# valid username reg-ex
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def is_valid_username(username):
    """Checks if the username is valid using reg-ex

    Args:
        username (string): The user's name

    Returns:
        The True if the username is valid
    """
    return username and USER_RE.match(username)

# valid password reg-ex
PASS_RE = re.compile(r"^.{3,20}$")
def is_valid_password(password):
    """Checks if the password is valid using reg-ex

    Args:
        password (string): The user's password

    Returns:
        The True if the password is valid
    """
    return password and PASS_RE.match(password)

# valid email reg-ex
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def is_valid_email(email):
    """Checks if the email is valid using reg-ex

    Args:
        email (string): The user's email

    Returns:
        The True if the email is valid
    """
    return not email or EMAIL_RE.match(email)
