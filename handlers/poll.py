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

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import os.path
import yaml

import oauth
import buzz

import web.helper
import models.tokens
import models.board

OAUTH_CONFIG = yaml.load(open('oauth.yaml').read())

OAUTH_CONSUMER_KEY = OAUTH_CONFIG['oauth_consumer_key']
OAUTH_CONSUMER_SECRET = OAUTH_CONFIG['oauth_consumer_secret']
OAUTH_TOKEN_KEY = OAUTH_CONFIG['oauth_token_key']
OAUTH_TOKEN_SECRET = OAUTH_CONFIG['oauth_token_secret']

class PollHandler(webapp.RequestHandler):
  @property
  def client(self):
    if not hasattr(self, '_client') or not self._client:
      access_token = oauth.OAuthToken(OAUTH_TOKEN_KEY, OAUTH_TOKEN_SECRET)
      self._client = buzz.Client()
      self._client.build_oauth_consumer(
        OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET
      )
      self._client.oauth_access_token = access_token
      self._client.oauth_scopes.append(buzz.FULL_ACCESS_SCOPE)
    return self._client
  
  def get(self):
    template_values = {
      'http_get': True,
      'message': None
    }
    path = os.path.join(
      os.path.dirname(__file__), '..', 'templates', 'poll.html'
    )
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    # Due to a bug, we can't use mentions and the consumption feed
    # posts = self.client.posts('@consumption')
    # Using the #buzzbingo hashtag instead
    posts = self.client.search(query="buzzbingo")
    message = 'Retrieved %d posts.' % len(posts)
    template_values = {
      'http_get': False,
      'message': message
    }
    path = os.path.join(
      os.path.dirname(__file__), '..', 'templates', 'poll.html'
    )
    self.response.out.write(template.render(path, template_values))
