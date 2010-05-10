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
