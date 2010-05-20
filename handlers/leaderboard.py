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

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import os.path
import logging

import models.badge
import models.player

class LeaderboardHandler(webapp.RequestHandler):
  def get(self):
    query = db.Query(models.player.Player)
    query.order('-bingo_count')
    top_players = query.fetch(limit=20)
    template_values = {
      'top_players': top_players
    }
    path = os.path.join(
      os.path.dirname(__file__), '..', 'templates', 'leaderboard.html'
    )
    self.response.out.write(template.render(path, template_values))
