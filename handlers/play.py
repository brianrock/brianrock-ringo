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

import web.helper
import models.tokens
import models.board

class PlayHandler(webapp.RequestHandler):
  def get(self):
    cookies = web.helper.parse_cookies(self)
    if cookies:
      db_access_token = models.tokens.AccessToken.from_key(
        cookies.get('access_token')
      )
      if db_access_token:
        player = db_access_token.player
        board = player.board
        template_values = {
          'player': player,
          'board': board
        }
        path = os.path.join(
          os.path.dirname(__file__), '..', 'templates', 'board.html'
        )
        self.response.out.write(template.render(path, template_values))
        # self.response.out.write('Player: ' + str(db_access_token.player))
      else:
        self.response.out.write('Player doesn\'t exist')
    else:
      self.redirect('/oauth/init/')
