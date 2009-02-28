#!/usr/bin/env python

"""
PayPal utility class based on http://www.djangosnippets.org/snippets/1181/
modified to use the urlfetch API which is part of App Engine and to move
configuration into a settings module
"""

import urllib, md5, datetime, sys
from cgi import parse_qs
import logging

from google.appengine.api import urlfetch

# You need a settings.py file in the root of your site which defines
# the following constant: PAYPAL_USER, PAYPAL_PASSWORD, PAYPAL_SIG, 
# PAYPAL_RETURNURL, PAYPAL_CANCELURL
try:
    import settings
except ImportError, error:
    logging.error("You have to create a local settings file (Error: %s)" % error)
    sys.exit()

class PayPal:
    signature_values = {}
    API_ENDPOINT = "https://api-3t.sandbox.paypal.com/nvp"
    PAYPAL_URL = "https://www.sandbox.paypal.com/webscr&cmd=_express-checkout&token="
    
    def __init__(self):
        self.signature_values = {
            'USER' : settings.PAYPAL_USER, 
            'PWD' : settings.PAYPAL_PASSWORD, 
            'SIGNATURE' : settings.PAYPAL_SIG,
            'VERSION' : '53.0',
        }
        self.signature = urllib.urlencode(self.signature_values) + "&"
        
    def SetExpressCheckout(self, amount, **kwargs):
        params = {
            'METHOD' : "SetExpressCheckout",
            'NOSHIPPING' : 1,
            'PAYMENTACTION' : 'Authorization',
            'RETURNURL' : settings.PAYPAL_RETURNURL,
            'CANCELURL' : settings.PAYPAL_CANCELURL,
            'AMT' : amount,
        }
        params.update(kwargs)
        params_string = self.signature + urllib.urlencode(params)
        url = "%s?%s" % (self.API_ENDPOINT, params_string)
        response = urlfetch.fetch(url)                
        response_dict = parse_qs(response.content)
        response_token = response_dict['TOKEN'][0]
        return response_token
    
    def GetExpressCheckoutDetails(self, token, return_all = False):
        params = {
            'METHOD' : "GetExpressCheckoutDetails",
            'RETURNURL' : settings.PAYPAL_RETURNURL,
            'CANCELURL' : settings.PAYPAL_CANCELURL,
            'TOKEN' : token,
        }
        params_string = self.signature + urllib.urlencode(params)        
        url = "%s?%s" % (self.API_ENDPOINT, params_string)
        response = urlfetch.fetch(url)                
        response_dict = parse_qs(response.content)
        if return_all:
            return response_dict
        try:
            response_token = response_dict['TOKEN'][0]
        except KeyError:
            response_token = response_dict
        return response_token
    
    def DoExpressCheckoutPayment(self, token, payer_id, amt):
        params = {
            'METHOD' : "DoExpressCheckoutPayment",
            'PAYMENTACTION' : 'Sale',
            'RETURNURL' : settings.PAYPAL_RETURNURL,
            'CANCELURL' : settings.PAYPAL_CANCELURL,
            'TOKEN' : token,
            'AMT' : amt,
            'PAYERID' : payer_id,
        }
        params_string = self.signature + urllib.urlencode(params)
        url = "%s?%s" % (self.API_ENDPOINT, params_string)
        response = urlfetch.fetch(url)                
        response_tokens = {}
        for token in response.content.split('&'):
            response_tokens[token.split("=")[0]] = token.split("=")[1]
        for key in response_tokens.keys():
                response_tokens[key] = urllib.unquote(response_tokens[key])
        return response_tokens
        
    def GetTransactionDetails(self, tx_id):
        params = {
            'METHOD' : "GetTransactionDetails", 
            'TRANSACTIONID' : tx_id,
        }
        params_string = self.signature + urllib.urlencode(params)
        url = "%s?%s" % (self.API_ENDPOINT, params_string)
        response = urlfetch.fetch(url)                
        response_tokens = {}
        for token in response.content.split('&'):
            response_tokens[token.split("=")[0]] = token.split("=")[1]
        for key in response_tokens.keys():
                response_tokens[key] = urllib.unquote(response_tokens[key])
        return response_tokens