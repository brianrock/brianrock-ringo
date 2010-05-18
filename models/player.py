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

import models.tokens
import models.board
import models.scored_post

import copy
import random
import yaml

import buzz

OAUTH_CONFIG = yaml.load(open('oauth.yaml').read())

OAUTH_CONSUMER_KEY = OAUTH_CONFIG['oauth_consumer_key']
OAUTH_CONSUMER_SECRET = OAUTH_CONFIG['oauth_consumer_secret']
OAUTH_TOKEN_KEY = OAUTH_CONFIG['oauth_token_key']
OAUTH_TOKEN_SECRET = OAUTH_CONFIG['oauth_token_secret']

class Player(db.Model):
  name = db.StringProperty()

  def __init__(self, parent=None, key_name=None, **kwds):
    db.Model.__init__(self, parent, key_name, **kwds)
    self._board = None
    self._topics = None

  def __repr__(self):
    return "<Player[%s, %s]>" % (self.name, self.key().name())

  @property
  def oauth_access_token(self):
    query = db.Query(models.tokens.AccessToken)
    query.filter('player_id =', self.key().name())
    results = query.fetch(limit=1)
    if results:
      return results[0]
    else:
      return None

  def square_for_topic(self, topic):
    for x in xrange(5):
      for y in xrange(5):
        if self.board[x][y] and self.board[x][y].topic.lower().strip() == topic.lower().strip():
          return self.board[x][y]
    return None

  def has_post_scored(self, post_id):
    if isinstance(post_id, buzz.Post):
      post_id = post_id.id
    query = db.Query(models.scored_post.ScoredPost)
    query.ancestor(self)
    query.filter('post_id =', post_id)
    results = query.fetch(limit=1)
    return not not results

  def score_post(self, post_id, post_uri, topic):
    scored_post = models.scored_post.ScoredPost(
      parent=self,
      post_id=post_id,
      topic=topic
    )
    scored_post.put()
    square = self.square_for_topic(topic)
    square.post_id = post_id
    square.post_uri = post_uri
    square.put()
    # Check for badge conditions being met
    score_count = 0
    horizontal_counts = [0, 0, 0, 0, 0] # Indexed by y-axis
    vertical_counts   = [0, 0, 0, 0, 0] # Indexed by x-axis
    for x in xrange(5):
      for y in xrange(5):
        if self.board[x][y] and self.board[x][y].post_id:
          score_count + 1
          horizontal_counts[y] += 1
          vertical_counts[x] += 1

  @property
  def badges(self):
    if not self._badges:
      query = db.Query(models.badge.Badge)
      query.ancestor(self)
      self._badges = query.fetch(limit=1000) # Hey, it could happen.
    return self._badges

  @property
  def topics(self):
    if not self._topics:
      self._topics = []
      for x in xrange(5):
        for y in xrange(5):
          if self.board[x][y]:
            self._topics.append(self.board[x][y].topic)
    return self._topics

  @property
  def board(self):
    if not self._board:
      query = db.Query(models.board.Square)
      query.ancestor(self)
      results = query.fetch(limit=24)
      self._board = [[None for _ in xrange(5)] for _ in xrange(5)]
      if results:
        if len(results) != 24:
          raise ValueError(
            'Bogus number of squares: %d (should be 24)' % len(results)
          )
        # Board already exists for this player
        while results:
          square = results.pop()
          x, y = square.key().name().split(':')
          x, y = int(x), int(y)
          if x == 2 and y == 2:
            raise ValueError(
              'Topic square in datastore where Free Space should be.'
            )
          self._board[x][y] = square
      else:
        # Create a new board
        topic_choices = copy.copy(models.board.TOPIC_LIST)
        topics = []
        # Select 24 topics at random.  Center square is free space.
        while(topic_choices and len(topics) < 24):
          element = random.choice(topic_choices)
          topic_choices.remove(element)
          topics.append(element)
        if len(topics) != 24:
          raise ValueError('Not enough topics: %d (should be 24)' % len(topics))
        for x in xrange(5):
          for y in xrange(5):
            if x != 2 or y != 2:
              # We leave the "Free Space" as None
              square = models.board.Square(
                parent=self,
                key_name=('%d:%d' % (x, y)),
                topic=topics.pop()
              )
              square.put()
              self._board[x][y] = square
    return self._board
