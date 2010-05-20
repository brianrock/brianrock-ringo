#!/usr/bin/env python
#
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

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import handlers.intro
import handlers.oauth
import handlers.play
import handlers.leaderboard
import handlers.poll

def main():
  application = webapp.WSGIApplication([
    ('/', handlers.intro.IntroHandler),
    ('/oauth/init/', handlers.oauth.OAuthInitHandler),
    ('/oauth/callback/', handlers.oauth.OAuthCallbackHandler),
    ('/worker/poll/', handlers.poll.PollHandler),
    ('/play/', handlers.play.PlayHandler),
    ('/leaderboard/', handlers.leaderboard.LeaderboardHandler)
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
