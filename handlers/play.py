from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import os.path

import web.helper
import models.tokens

class PlayHandler(webapp.RequestHandler):
  def get(self):
    cookies = web.helper.parse_cookies(self)
    if cookies:
      db_access_token = models.tokens.AccessToken.from_key(
        cookies.get('access_token')
      )
      if db_access_token:
        template_values = {}
        path = os.path.join(
          os.path.dirname(__file__), '..', 'templates', 'board.html'
        )
        self.response.out.write(template.render(path, template_values))
        # self.response.out.write('Player: ' + str(db_access_token.player))
      else:
        self.response.out.write('Player doesn\'t exist')
    else:
      self.redirect('/oauth/init/')
