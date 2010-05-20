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
from google.appengine.api.labs import taskqueue

import os.path
import logging
import yaml

import web.helper
import models.tokens
import models.board

PRIORITY_PROFILES = yaml.load(open('polling.yaml').read())

class PlayHandler(webapp.RequestHandler):
  def get(self):
    cookies = web.helper.parse_cookies(self)
    if cookies:
      db_access_token = models.tokens.AccessToken.from_key(
        cookies.get('access_token')
      )
      if db_access_token:
        player = db_access_token.player
        logging.info('\'%s\' is playing the game!' % player.name)
        board = player.board
        template_values = {
          'player': player,
          'board': board
        }
        path = os.path.join(
          os.path.dirname(__file__), '..', 'templates', 'board.html'
        )
        if player.profile_name in PRIORITY_PROFILES:
          logging.info('Auto-polled user is playing.  Enqueuing...')
          try:
            result_task = taskqueue.Task(url='/worker/poll/')
            result_task.add()
          except Exception, e:
            # Eat all errors here, because we really just don't care what
            # happened.  We're just happy if we can poll faster than once
            # a minute.
            logging.error(str(e))
            result_task = None
        
        self.response.out.write(template.render(path, template_values))
      else:
        web.helper.clear_oauth_token_cookies(self)
        self.redirect('/oauth/init/')
    else:
      web.helper.clear_oauth_token_cookies(self)
      self.redirect('/oauth/init/')
