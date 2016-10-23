import os
import jinja2
import hmac

SECRET = 'qkp0Vr0OY8nnB0eM0ddJIKLxkXkLW8SuCnoa7QCP'

template_dir = os.path.join(os.path.dirname(__file__), "html")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def render_str(template, **params):
    """Renders a Jinja HTML template using the given params

    Args:
        template (string): filename of the template
        **params: keywords used to populate template

    Returns:
        Rendered HTML with the parameters provided.
    """
    t = jinja_env.get_template(template)
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
