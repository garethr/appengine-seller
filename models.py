from google.appengine.ext import db
from google.appengine.api.users import User

class Purchase(db.Model):
    "Represents a purchase order from PayPal"
    first_name = db.StringProperty(required=True)
    last_name = db.StringProperty(required=True)
    amount = db.FloatProperty(required=True)
    email = db.EmailProperty(required=True)
    payer_id = db.IntegerProperty(required=True)
    currency = db.StringProperty(required=True)
    correlation_id = db.IntegerProperty(required=True)
    # we store the date automatically so we can filter the list
    # but this isn't provided by the API
    date = db.DateTimeProperty(auto_now_add=True)
    # we should check this carefully as it appears the hash
    # has been changed
    tampering = db.BooleanProperty(default=False)
    # when true this means that paypal has confirmed the payment
    payment_recieved = db.BooleanProperty(default=False)
    # we have processed this order
    processed = db.BooleanProperty(default=False)