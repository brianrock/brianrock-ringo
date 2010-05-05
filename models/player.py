from google.appengine.ext import db

import models.tokens
import models.board

import copy
import random

# TODO: Needs more topics
TOPIC_LIST = [
  "App Engine",
  "Buzz",
  "PubSubHubbub",
  "Salmon",
  "Android",
  "Enterprise Marketplace",
  "ChromeOS",
  "Chrome Extensions",
  "HTML5",
  "Chrome Frame",
  "Cloud Computing",
  "GWT",
  "Maps",
  "Social Web",
  "KML",
  "PowerMeter",
  "YouTube",
  "Google Chart Tools",
  "Google Analytics",
  "Activity Streams",
  "MediaRSS",
  "XFN",
  "OAuth",
  "OpenID",
  "Native Client",
  "iGoogle",
  "Closure",
  "OpenSocial",
  "Wave",
  "Page Speed",
  "Speed Tracer",
  "SEO"
]

class Player(db.Model):
  @property
  def oauth_access_token(self):
    return self.parent()
    
  @property
  def board(self):
    query = db.Query(models.board.Square)
    query.ancestor(self)
    results = query.fetch(limit=24)
    board = [[None for _ in xrange(5)] for _ in xrange(5)]
    if len(results) != 24:
      raise ValueError(
        'Bogus number of squares: %d (should be 24)' % len(results)
      )
    if results:
      # Board already exists for this player
      while results:
        square = results.pop()
        x, y = square.key().name().split(':')
        x, y = int(x), int(y)
        if x == 2 and y == 2:
          raise ValueError(
            'Topic square in datastore where Free Space should be.'
          )
        board[x][y] = square
    else:
      # Create a new board
      topic_choices = copy.copy(TOPIC_LIST)
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
          if x != 2 and y != 2:
            square = models.board.Square(
              parent=self,
              key_name=('%d:%d' % (x, y)),
              topic=topics.pop()
            )
            square.put()
            board[x][y] = square
    return board
