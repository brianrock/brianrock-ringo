from google.appengine.ext import db

import models.player

class Square(db.Model):
  # The player is the square's parent.
  topic = db.StringProperty()

  @property
  def player(self):
    return self.parent()
