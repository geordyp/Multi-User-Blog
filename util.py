import os
import hmac
import jinja2
import re

SECRET = 'qkp0Vr0OY8nnB0eM0ddJIKLxkXkLW8SuCnoa7QCP'

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "html")
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR), autoescape=True)

def render_str(template, **params):
    """Renders a Jinja HTML template using the given params

    Args:
        template (string): filename of the template
        **params: keywords used to populate template

    Returns:
        Rendered HTML with the parameters provided.
    """
    t = JINJA_ENV.get_template(template)
    return t.render(params)

def make_secure_val(val):
    """Creates a secure cookie value

    Args:
        val (string): The cookie's value

    Returns:
        A hashed value
    """
    return "%s|%s" % (val, hmac.new(SECRET, val).hexdigest())

def check_secure_val(secure_val):
    """Checks a cookie value to ensure security

    Args:
        secure_val (string): The value to check

    Returns:
        The value if secure
    """
    val = secure_val.split("|")[0]
    if secure_val == make_secure_val(val):
        return val

def is_valid_username(username):
    """Checks if the username is valid using reg-ex

    Args:
        username (string): The user's name

    Returns:
        The True if the username is valid
    """
    # valid username reg-ex
    user_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return username and user_re.match(username)

def is_valid_password(password):
    """Checks if the password is valid using reg-ex

    Args:
        password (string): The user's password

    Returns:
        The True if the password is valid
    """
    # valid password reg-ex
    pass_re = re.compile(r"^.{3,20}$")
    return password and pass_re.match(password)

def is_valid_email(email):
    """Checks if the email is valid using reg-ex

    Args:
        email (string): The user's email

    Returns:
        The True if the email is valid
    """
    # valid email reg-ex
    email_re = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return not email or email_re.match(email)
