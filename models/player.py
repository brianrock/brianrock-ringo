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
from google.appengine.api.labs import taskqueue

import models.tokens
import models.board
import models.scored_post
import models.badge

import copy
import random
import yaml
import logging

import buzz

OAUTH_CONFIG = yaml.load(open('oauth.yaml').read())

OAUTH_CONSUMER_KEY = OAUTH_CONFIG['oauth_consumer_key']
OAUTH_CONSUMER_SECRET = OAUTH_CONFIG['oauth_consumer_secret']
OAUTH_TOKEN_KEY = OAUTH_CONFIG['oauth_token_key']
OAUTH_TOKEN_SECRET = OAUTH_CONFIG['oauth_token_secret']

VENUE_GEOCODE=('37.782058', '-122.404761')
VENUE_PLACE_ID='CmReAAAA0GxRE-AcdpB-0Xn65jNPOcnQj-qWyoWRBoarUGzprN9mn83spvD5zpgaeorfh242yEI8Zg7GLI2ccJcskAix1hQbH7otb7gLLB9QSvENSCuEqzB0Uz891Y5Y4MERKaatEhDddmbyctP_irYfMYE04owqGhT2pZLL4QnwbuUWzq8sKi8a45FDwg'

def _word_count(text):
  return len(text.strip().split(' '))

class Player(db.Model):
  name = db.StringProperty()
  profile_uri = db.StringProperty(required=True)
  profile_name = db.StringProperty(required=False)
  bingo_count = db.IntegerProperty(default=0)

  def __init__(self, parent=None, key_name=None, **kwds):
    db.Model.__init__(self, parent, key_name, **kwds)
    self._client = None
    self._board = None
    self._topics = None
    self._badges = None
    self._badges_awarded = set([])

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

  @property
  def client(self):
    if not self._client:
      self._client = buzz.Client()
      self._client.build_oauth_consumer(OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET)
      # We don't want to use the player's token, since we're going to post
      # new entries with it.
      self._client.build_oauth_access_token(OAUTH_TOKEN_KEY, OAUTH_TOKEN_SECRET)
      self._client.oauth_scopes.append(buzz.FULL_ACCESS_SCOPE)
    return self._client

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

  def award_badge(self, badge_type):
    badge = models.badge.Badge(
      parent=self,
      badge_type=badge_type
    )
    badge.put()
    logging.info(badge.badge_title)
    # Reset the badge list
    self._badges = None
    if not badge_type in self._badges_awarded:
      self._badges_awarded.add(badge_type)
      try:
        if self.profile_name:
          post_content = \
            '@%s@gmail.com has just earned the \'%s\' badge on Buzz Bingo!' % (
              self.profile_name, badge.badge_title
            )
        else:
          post_content = '%s has just earned the \'%s\' badge on Buzz Bingo!' % (
            self.name, badge.badge_title
          )
        badge_attachment = buzz.Attachment(
          type='photo', enclosure=badge.badge_icon
        )
        link_attachment = buzz.Attachment(
          type='article',
          title='Buzz Bingo',
          uri='http://buzz-bingo.appspot.com/'
        )
        badge_post = buzz.Post(
          content=post_content,
          attachments=[
            badge_attachment,
            link_attachment
          ],
          geocode=VENUE_GEOCODE,
          place_id=VENUE_PLACE_ID
        )
        self.client.create_post(badge_post)
      except Exception, e:
        logging.warning('Post was not created.')
        logging.error(e)

  def score_post(self, post, topic):
    self.award_content_badges(post)
    self.update_square(post, topic)
    self.award_score_badges()
    if not self._board:
      self.regenerate_board()

  def verify_bingo(self):
    self.award_score_badges()
    if not self._board:
      self.regenerate_board()

  def award_leader_badge(self):
    if not self.has_badge('leader'):
      query = db.Query(Player)
      query.order('-bingo_count')
      results = query.fetch(limit=1)
      if results and results[0].key().name() == self.key().name():
        self.award_badge('leader')

  def update_square(self, post, topic):
    scored_post = models.scored_post.ScoredPost(
      parent=self,
      post_id=post.id,
      topic=topic
    )
    scored_post.put()
    if topic != 'taco':
      square = self.square_for_topic(topic)
      square.post_id = post.id
      square.post_uri = post.uri
      square.put()
      # Update the board with the new square
      x, y = square.key().name().split(':')
      x, y = int(x), int(y)
      self._board[x][y] = square

  def award_score_badges(self):
    score_count = 0
    horizontal_counts = [0, 0, 1, 0, 0] # Indexed by y-axis
    vertical_counts   = [0, 0, 1, 0, 0] # Indexed by x-axis
    for x in xrange(5):
      for y in xrange(5):
        if self.board[x][y] and self.board[x][y].post_id:
          score_count += 1
          horizontal_counts[y] += 1
          vertical_counts[x] += 1
    if score_count >= 1 and not self.has_badge('hello-world'):
      self.award_badge('hello-world')
    if (5 in horizontal_counts) or (5 in vertical_counts):
      self.award_badge('bingo')
      if not hasattr(self, 'bingo_count') or not self.bingo_count:
        self.bingo_count = 0
      self.bingo_count += 1
      self.put()
      # Clear the board and reset.
      self._board = None

  def award_content_badges(self, post):
    if _word_count(post.content) > 100 and post.actor.id == self.key().name():
      self.award_badge('scholar')
    else:
      for comment in post.comments():
        logging.info(_word_count(comment.content))
        if _word_count(comment.content) > 100 and \
            comment.actor.id == self.key().name():
          self.award_badge('scholar')
          break
    if 'taco' in post.content.lower() and post.actor.id == self.key().name():
      self.award_badge('taco')
    else:
      for comment in post.comments():
        if 'taco' in comment.content.lower() and \
            comment.actor.id == self.key().name():
          self.award_badge('taco')
          break
    if post.attachments:
      for attachment in post.attachments:
        if attachment.type == 'article':
          self.award_badge('share')
          break
    if post.geocode and post.actor.id != self.key().name():
      self.award_badge('geo')
    elif post.geocode and post.actor.id == self.key().name():
      self.award_badge('mobile')

  def has_badge(self, badge_type):
    for badge in self.badges:
      if badge.badge_type == badge_type:
        return True
    return False

  @property
  def badges(self):
    if not self._badges:
      query = db.Query(models.badge.Badge)
      query.ancestor(self)
      query.order('date_awarded')
      self._badges = query.fetch(limit=1000) # Hey, it could happen.
    return self._badges

  @property
  def badge_list(self):
    return ', '.join(["'%s'" % badge.badge_title for badge in self.badges])

  @property
  def topics(self):
    if not self._topics:
      self._topics = ['taco']
      for x in xrange(5):
        for y in xrange(5):
          if self.board[x][y]:
            self._topics.append(self.board[x][y].topic)
    return self._topics

  def regenerate_board(self):
    # Clear the board and reset.
    self._board = None
    query = db.Query(models.board.Square)
    query.ancestor(self)
    results = query.fetch(limit=1000)
    db.delete(results)
    return self.board

  @property
  def board(self):
    if not self._board:
      query = db.Query(models.board.Square)
      query.ancestor(self)
      results = query.fetch(limit=24)
      self._board = [[None for _ in xrange(5)] for _ in xrange(5)]
      if results:
        if len(results) != 24:
          try:
            # We've got some kind of weird state in the data store.
            # Rescan because it should fixed itself in a moment.
            result_task = taskqueue.Task(url='/worker/poll/')
            result_task.add()
          except Exception, e:
            # Ignore all errors.
            result_task = None
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
