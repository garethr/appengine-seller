#!/usr/bin/env python

import os
import sys
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import urlfetch

# You need a settings.py file in the root of your site which defines
# the following constant: PAYPAL_USER, PAYPAL_PASSWORD, PAYPAL_SIG, 
# PAYPAL_RETURNURL, PAYPAL_CANCELURL, SALT
try:
    import settings
except ImportError, error:
    logging.error("You have to create a local settings file (Error: %s)" % error)
    sys.exit()

import paypal

class Index(webapp.RequestHandler):
    def get(self):
        """
        View demonstrating getting a token from paypal 
        and showing a link to purchase on the front end
        """
        # how much does your item cost?
        amount = 10
        # set the default context
        context = {}
        # the following will try and connect to paypal in order
        # to get a token. If we don't get anything back
        # we should at least handle it gracefully
        try:
            pp = paypal.PayPal()
            token = pp.SetExpressCheckout(amount)
            paypal_url = pp.PAYPAL_URL + token
            context.update({
                'paypal_url': paypal_url
            })
        except urlfetch.DownloadError:
            # log error
            pass
            
        # calculate the template path
        path = os.path.join(os.path.dirname(__file__), 'templates',
            'index.html')
        # render the template with the provided context
        output = template.render(path, context)
        self.response.out.write(output)
        
class Success(webapp.RequestHandler):
    def get(self):
        """
        This view deals with a successful returning visitor from paypal
        it should provide a form allowing the visitor to confirm 
        the purchase
        """
        # get the token from the query string
        token = self.request.get('token', '')
        # try and get in touch with paypal
        try:
            pp = paypal.PayPal()
            # get the details about what happened when our customer
            # was on paypal
            paypal_details = pp.GetExpressCheckoutDetails(token, return_all = True)
            connected = True
        except urlfetch.DownloadError:
            connected = False
        
        if connected and 'Success' in paypal_details['ACK']: 
            # this means not only did we get to talk to PayPal
            # but everything appears good. We should give them the
            # form to confirm payment
            token = paypal_details['TOKEN'][0]
            first_name = paypal_details['FIRSTNAME'][0]
            last_name = paypal_details['LASTNAME'][0]
            amount = paypal_details['AMT'][0]
            email = paypal_details['EMAIL'][0]
            payer_id = paypal_details['PAYERID'][0]
    
            # for added security we're creating a hash at this stage
            # and then comparing it again when we do the transation
            security = hash(amount + settings.SALT + payer_id)
            # store it for up to a day
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
            
        elif connected and 'Failure' in paypal_details['ACK']: 
            # this means we talked to paypal but something went wrong
            # it could be things like someone hacking the urls
            # resulting in invalid tokens
            # we should log this as an error
            severity = paypal_details['L_SEVERITYCODE0'][0]
            short_message = paypal_details['L_SHORTMESSAGE0'][0]
            long_message = paypal_details['L_LONGMESSAGE0'][0]
            error_code = paypal_details['L_ERRORCODE0'][0]
            correlation_id = paypal_details['CORRELATIONID'][0]
        else:
            context = {
                'paypal_details': paypal_details,
            }
            
        if not connected:
            # we couln't get through to paypal
            context = {
                'paypal_details': paypal_details,
            }
            
        # calculate the template path
        path = os.path.join(os.path.dirname(__file__), 'templates',
            'confirm.html')
        # render the template with the provided context
        output = template.render(path, context)
        self.response.out.write(output)
            
    def post(self):
        """
        This view deals with making the payment
        """
        # get data from the form
        token = self.request.POST.get('token', '')
        amount = self.request.POST.get('amount', '')
        payer_id = self.request.POST.get('payer_id', '')
        
        if token and amount and payer_id:
            # everything we need is present in the form data so we can proceed
            try:
                pp = paypal.PayPal()
                payment_details = pp.DoExpressCheckoutPayment(token=token, payer_id=payer_id, amt=amount)
                connected = True
            except urlfetch.DownloadError:
                # we coudn't get through to paypal
                connected = False

            if connected and 'Success' in payment_details['ACK']:
                # get our cached hash value
                data = memcache.get(token)
                if data is not None:
                    # do our hash calculations again
                    security = hash(amount + settings.SALT + payer_id)
                    if data == security:
                        # We have been paid. Do things like, enable subsciprion, ship goods etc.
                        template_file = 'success.html'
                else:
                    # the hash didn't exist, which probably means
                    # something has been tampered with
                    # log it
                    template_file = 'failure.html'
                        
            elif connected and 'Failure' in payment_details['ACK']:
                # this means we talked to paypal but something went wrong
                # it could be things like someone hacking the urls
                # resulting in invalid tokens
                severity = paypal_details['L_SEVERITYCODE0'][0]
                short_message = paypal_details['L_SHORTMESSAGE0'][0]
                long_message = paypal_details['L_LONGMESSAGE0'][0]
                error_code = paypal_details['L_ERRORCODE0'][0]
                correlation_id = paypal_details['CORRELATIONID'][0]
                # we should log this as an error            
                template_file = 'failure.html'
            
            if not connected:
                # we couln't get through to paypal
                # log it
                template_file = 'failure.html'
                
        else:
            # something was missing from the form data
            # we might be able to try again but 
            # this is probably either a client issue or
            # someone playing silly buggers
            self.redirect('/returnurl?%s' % token)
            return

        context = {
            'payment_details': payment_details,
        }
            
        # calculate the template path
        path = os.path.join(os.path.dirname(__file__), 'templates',
            template_file)
        # render the template with the provided context
        output = template.render(path, context)
        self.response.out.write(output)      

class Cancel(webapp.RequestHandler):
    def get(self):
        """
        This view deals with the situation if people
        visit paypal but click the cancel button
        """
        # calculate the template path
        path = os.path.join(os.path.dirname(__file__), 'templates',
            'index.html')
        # render the template with the provided context
        output = template.render(path, context)
        self.response.out.write(output)      

# wire up the views
application = webapp.WSGIApplication([
    ('/', Index),
    ('/returnurl', Success),
    ('/cancelurl', Cancel),
], debug=True)

def main():
    "Run the application"
    run_wsgi_app(application)

if __name__ == '__main__':
    main()