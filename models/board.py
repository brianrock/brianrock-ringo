from google.appengine.ext import db

import models.player

import urllib

import django.template

register = django.template.Library()

class Square(db.Model):
  # The player is the square's parent.
  topic = db.StringProperty()

  @property
  def player(self):
    return self.parent()

  @property
  def search_uri(self):
    return (
      "http://mail.google.com/mail/?shva=1#buzz/search/%s" %
        urllib.quote_plus(self.topic)
    )

@register.filter
def search_uri(square):
  """Returns the search_uri for a square."""
  if isinstance(square, Square):
    return square.search_uri
  else:
    raise TypeError('Must be a models.board.Square')

@register.filter
def topic(square):
  """Returns the topic for a square."""
  if isinstance(square, Square):
    return square.topic
  else:
    raise TypeError('Must be a models.board.Square')
