#!/usr/bin/env python

"""
PayPal utility class based on http://www.djangosnippets.org/snippets/1181/
and modified to use the urlfetch API which is part of App Engine
"""

import urllib, md5, datetime
from cgi import parse_qs

from google.appengine.api import urlfetch

class PayPal:
    signature_values = {}
    API_ENDPOINT = "https://api-3t.sandbox.paypal.com/nvp"
    PAYPAL_URL = "https://www.sandbox.paypal.com/webscr&cmd=_express-checkout&token="
    
    def __init__(self):
        ## Sandbox values
        self.signature_values = {
            'USER' : 'gareth_1235331656_biz_api1.gmail.com', #'sdk-three_api1.sdk.com',
            'PWD' : '1235331680', #'QFZCWN5HZM8VBG7Q',
            'SIGNATURE' : 'AFcWxV21C7fd0v3bYYYRCpSSRl31ApqbGFJeDaKFcDnvrb89dJa.1YCv', #'A-IzJhZZjhg29XQ2qnhapuwxIDzyAZQ92FRP5dqBzVesOkzbdUONzmOU',
            'VERSION' : '53.0',
        }
        self.signature = urllib.urlencode(self.signature_values) + "&"
        
    def SetExpressCheckout(self, amount, **kwargs):
        params = {
            'METHOD' : "SetExpressCheckout",
            'NOSHIPPING' : 1,
            'PAYMENTACTION' : 'Authorization',
            'RETURNURL' : 'http://localhost:8080/returnurl',
            'CANCELURL' : 'http://localhost:8080/cancelurl',
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
            'RETURNURL' : 'http://localhost:8080/returnurl', #edit this 
            'CANCELURL' : 'http://localhost:8080/cancelurl', #edit this 
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
            'RETURNURL' : 'http://localhost:8080/returnurl', #edit this 
            'CANCELURL' : 'http://localhost:8080/cancelurl', #edit this 
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