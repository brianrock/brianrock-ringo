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

from google.appengine.ext import db

import oauth

import models.player

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
  def token(self):
    return oauth.OAuthToken(self.oauth_key, self.oauth_secret)

  def __repr__(self):
    return "<Token[%s, %s]>" % (self.oauth_key, self.oauth_secret)

class AccessToken(db.Model):
  # The player is the access token's parent.
  oauth_key = db.StringProperty()
  oauth_secret = db.StringProperty()

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
  def token(self):
    return oauth.OAuthToken(self.oauth_key, self.oauth_secret)

  @property
  def player(self):
    query = db.Query(models.player.Player)
    query.ancestor(self)
    result = query.fetch(limit=1)
    if result:
      # There should only ever be one player with this token as its ancestor
      return result[0]
    else:
      # There is no player for this token, so create one!
      player = models.player.Player(parent=self)
      player.put()
      return player

  def __repr__(self):
    return "<Token[%s, %s]>" % (self.oauth_key, self.oauth_secret)
