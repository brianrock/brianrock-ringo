# Copyright 2010 Google Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Needed to avoid ambiguity in imports
from __future__ import absolute_import

import yaml

from google.appengine.ext import db
from google.appengine.ext import webapp

import web.helper
import models.tokens

import buzz
import logging

OAUTH_CONFIG = yaml.load(open('oauth.yaml').read())

OAUTH_CONSUMER_KEY = OAUTH_CONFIG['oauth_consumer_key']
OAUTH_CONSUMER_SECRET = OAUTH_CONFIG['oauth_consumer_secret']
OAUTH_TOKEN_KEY = OAUTH_CONFIG['oauth_token_key']
OAUTH_TOKEN_SECRET = OAUTH_CONFIG['oauth_token_secret']

class OAuthInitHandler(webapp.RequestHandler):  
  @property
  def client(self):
    if not hasattr(self, '_client') or not self._client:
      self._client = buzz.Client()
      self._client.build_oauth_consumer(
        OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET
      )
      self._client.oauth_scopes.append(buzz.FULL_ACCESS_SCOPE)
    return self._client

  def get(self):
    # Begin the OAuth dance!
    cookies = web.helper.parse_cookies(self)
    if cookies:
      if cookies.get('access_token'):
        self.redirect('/play/')
        return
      elif cookies.get('request_token'):
        # This branch keeps us from generating lots of request tokens if
        # a user drops out of the OAuth flow and comes back.
        db_request_token = models.tokens.RequestToken.from_key(
          cookies.get('request_token')
        )
        if db_request_token:
          oauth_request_token = db_request_token.token
        else:
          # No record of this request token.
          # Clear cookie and redirect to self.
          web.helper.clear_oauth_token_cookies(self)
          self.redirect('/oauth/init/')
          return
        save_token = False
      else:
        # Eh?  What's going on?
        self.redirect('/huh?')
        return
    else:
      # TODO: Change this to production URL, don't hardcode it
      oauth_request_token = self.client.fetch_oauth_request_token(
        'http://localhost:8085/oauth/callback/'
      )
      save_token = True
    # Build the authorization URL and then redirect to it
    authorization_url = self.client.build_oauth_authorization_url(
      oauth_request_token
    )
    self.response.set_status(302)
    self.response.headers['Location'] = authorization_url
    web.helper.set_request_token_cookie(self, oauth_request_token)
    if save_token:
      db_request_token = models.tokens.RequestToken(
        oauth_key=oauth_request_token.key,
        oauth_secret=oauth_request_token.secret
      )
      db_request_token.put()
    return

class OAuthCallbackHandler(webapp.RequestHandler):
  @property
  def client(self):
    if not hasattr(self, '_client') or not self._client:
      logging.info('building client...')
      self._client = buzz.Client()
      self._client.build_oauth_consumer(
        OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET
      )
      self._client.oauth_scopes.append(buzz.FULL_ACCESS_SCOPE)
    return self._client

  def get(self):
    cookies = web.helper.parse_cookies(self)
    if cookies:
      if cookies.get('access_token'):
        self.redirect('/play/')
        return
      elif self.request.get('oauth_verifier'):
        verifier = self.request.get('oauth_verifier')
        request_token_key = self.request.get('oauth_token')
        db_request_token = models.tokens.RequestToken.from_key(
          cookies.get('request_token')
        )
        if db_request_token:
          # There should only ever be one request token
          oauth_request_token = db_request_token.token
          # Give the Buzz client our request token, then upgrade it to
          # an access token
          self.client.oauth_request_token = oauth_request_token
          oauth_access_token = self.client.fetch_oauth_access_token(verifier)

          # TODO: Create a player object

          # Save the access token, then delete the request token
          db_access_token = models.tokens.AccessToken(
            oauth_key=oauth_access_token.key,
            oauth_secret=oauth_access_token.secret
          )
          db_access_token.put()
          db_request_token.delete()
          web.helper.set_access_token_cookie(self, oauth_access_token)
          self.redirect('/play/')
        else:
          # Epic fail. Unknown request token.
          web.helper.clear_oauth_token_cookies(self)
          self.redirect('/oauth/init/')
          return
      else:
        # Epic fail. Page visited without parameters.
        web.helper.clear_oauth_token_cookies(self)
        self.redirect('/oauth/init/')
        return
