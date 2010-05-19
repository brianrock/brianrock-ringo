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

from google.appengine.ext import db

import yaml

import buzz
import oauth

import models.player

OAUTH_CONFIG = yaml.load(open('oauth.yaml').read())

OAUTH_CONSUMER_KEY = OAUTH_CONFIG['oauth_consumer_key']
OAUTH_CONSUMER_SECRET = OAUTH_CONFIG['oauth_consumer_secret']
OAUTH_TOKEN_KEY = OAUTH_CONFIG['oauth_token_key']
OAUTH_TOKEN_SECRET = OAUTH_CONFIG['oauth_token_secret']

class RequestToken(db.Model):
  # The player is the request token's parent.
  oauth_key = db.StringProperty()
  oauth_secret = db.StringProperty()

  @staticmethod
  def from_key(oauth_key):
    query = db.Query(RequestToken)
    query.filter('oauth_key =', oauth_key)
    results = query.fetch(limit=1)
    if results:
      return results[0]
    else:
      return None

  @property
  def player(self):
    return self.parent

  @property
  def token(self):
    return oauth.OAuthToken(self.oauth_key, self.oauth_secret)

  def __repr__(self):
    return "<Token[%s, %s]>" % (self.oauth_key, self.oauth_secret)

class AccessToken(db.Model):
  # The player is the access token's parent.
  oauth_key = db.StringProperty()
  oauth_secret = db.StringProperty()
  player_id = db.StringProperty()

  @staticmethod
  def from_key(oauth_key):
    query = db.Query(AccessToken)
    query.filter('oauth_key =', oauth_key)
    results = query.fetch(limit=1)
    if results:
      return results[0]
    else:
      return None

  @property
  def player(self):
    player = None
    if self.player_id:
      player = models.player.Player.get_by_key_name(self.player_id)
    if player:
      return player
    else:
      # There is no player for this token, so create one!
      client = buzz.Client()
      client.build_oauth_consumer(OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET)
      client.oauth_access_token = self.token
      client.oauth_scopes.append(buzz.FULL_ACCESS_SCOPE)
      person = client.person().data
      player = models.player.Player(
        key_name=person.id,
        name=person.name,
        profile_name=person.profile_name
      )
      player.put()
      self.player_id = person.id
      self.put()
      return player
      
  @property
  def token(self):
    return oauth.OAuthToken(self.oauth_key, self.oauth_secret)

  def __repr__(self):
    return "<Token[%s, %s]>" % (self.oauth_key, self.oauth_secret)
