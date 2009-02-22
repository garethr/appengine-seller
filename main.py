#!/usr/bin/env python

import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

import paypal

class Index(webapp.RequestHandler):
    def get(self):
        pp = paypal.PayPal()
        token = pp.SetExpressCheckout(10)
        paypal_url = pp.PAYPAL_URL + token
        context = {
            'paypal_url': paypal_url
        }
        # calculate the template path
        path = os.path.join(os.path.dirname(__file__), 'templates',
            'index.html')
        # render the template with the provided context
        output = template.render(path, context)
        self.response.out.write(output)
        
class Success(webapp.RequestHandler):
    def get(self):
        token = self.request.get('token', '')
        pp = paypal.PayPal()
        paypal_details = pp.GetExpressCheckoutDetails(token, return_all = True)
        # if 'Success' in paypal_details['ACK']:
        
        token = paypal_details['TOKEN'][0]
        first_name = paypal_details['FIRSTNAME'][0]
        last_name = paypal_details['LASTNAME'][0]
        amount = paypal_details['AMT'][0]
        email = paypal_details['EMAIL'][0]
        payer_id = paypal_details['PAYERID'][0]
        
        security = hash(amount + payer_id)
        memcache.add(token, security, 360)
        
        context = {
            'paypal_details': paypal_details,
            'token': token,
            'first_name': first_name,
            'last_name': last_name,
            'amount': amount,
            'email': email,    
            'payer_id': payer_id,
        }
        # calculate the template path
        path = os.path.join(os.path.dirname(__file__), 'templates',
            'confirm.html')
        # render the template with the provided context
        output = template.render(path, context)
        self.response.out.write(output)
            
    def post(self):
        token = self.request.POST.get('token', '')
        amount = self.request.POST.get('amount', '')
        payer_id = self.request.POST.get('payer_id', '')
        pp = paypal.PayPal()
        payment_details  = pp.DoExpressCheckoutPayment(token=token, payer_id=payer_id, amt=amount)
        
        template_file = 'failure.html'
        data = memcache.get(token)
        if 'Success' in payment_details['ACK']:
            if data is not None:
                security = hash(amount + payer_id)
                if data == security:
                    # We have been paid. DO things like, enable subsciprion, ship goods etc.
                    template_file = 'success.html'
            
        context = {
            'payment_details': payment_details,
        }
            
        # calculate the template path
        path = os.path.join(os.path.dirname(__file__), 'templates',
            template_file)
        # render the template with the provided context
        output = template.render(path, context)
        self.response.out.write(output)      

# wire up the views
application = webapp.WSGIApplication([
    ('/', Index),
    ('/returnurl', Success),
], debug=True)

def main():
    "Run the application"
    run_wsgi_app(application)

if __name__ == '__main__':
    main()