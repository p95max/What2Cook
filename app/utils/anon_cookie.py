import os
import uuid
from itsdangerous import URLSafeSerializer

SECRET = os.getenv("SECRET_KEY", "change_me_to_a_random_secret")
SALT = "anon-cookie-v1"
serializer = URLSafeSerializer(SECRET, salt=SALT)

def make_anon_cookie_val(anon_id):
    return serializer.dumps({"id": str(anon_id)})

def load_anon_cookie_val(val):
    try:
        data = serializer.loads(val)
        return data.get("id")
    except Exception:
        return None
