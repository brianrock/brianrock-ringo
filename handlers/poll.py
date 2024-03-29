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
from google.appengine.api.labs import taskqueue

import logging

import os.path
import yaml
import time
import random
import re

import oauth
import buzz

import web.helper
import models.tokens
import models.board

OAUTH_CONFIG = yaml.load(open('oauth.yaml').read())

OAUTH_CONSUMER_KEY = OAUTH_CONFIG['oauth_consumer_key']
OAUTH_CONSUMER_SECRET = OAUTH_CONFIG['oauth_consumer_secret']
OAUTH_TOKEN_KEY = OAUTH_CONFIG['oauth_token_key']
OAUTH_TOKEN_SECRET = OAUTH_CONFIG['oauth_token_secret']

PRIORITY_PROFILES = yaml.load(open('polling.yaml').read())

BUZZ_BINGO_ID = '103831860836738334913'

class PollHandler(webapp.RequestHandler):
  @property
  def client(self):
    if not hasattr(self, '_client') or not self._client:
      access_token = oauth.OAuthToken(OAUTH_TOKEN_KEY, OAUTH_TOKEN_SECRET)
      self._client = buzz.Client()
      self._client.build_oauth_consumer(
        OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET
      )
      self._client.oauth_access_token = access_token
      self._client.oauth_scopes.append(buzz.FULL_ACCESS_SCOPE)
    return self._client

  @property
  def combined_results(self):
    if not hasattr(self, '_combined_results') or not self._combined_results:
      self._combined_results = []
      try:
        # Ignore the Buzz Bingo game itself
        for post in self.client.posts(type_id='@consumption'):
          if post.actor.id != BUZZ_BINGO_ID:
            self._combined_results.append(post)
        for post in self.client.search(query="buzzbingo"):
          if post.actor.id != BUZZ_BINGO_ID:          
            self._combined_results.append(post)
      except buzz.RetrieveError, e:
        logging.warning(str(e))
      logging.info('%d posts will be scored.' % len(self._combined_results))
    return self._combined_results

  def get(self):
    cron = False
    if self.request.headers.get('X-AppEngine-Cron') == 'true':
      cron = True
    elif self.request.headers.get('Referer') and \
        self.request.headers.get('Referer').find('/_ah/admin/cron') != -1:
      cron = True
    if cron:
      try:
        result_task = taskqueue.Task(url='/worker/poll/')
        result_task.add()
        logging.info('Polling task enqueued...')
      except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError), e:
        logging.error(str(e))
        result_task = None
    template_values = {
      'http_get': True,
      'message': None
    }
    path = os.path.join(
      os.path.dirname(__file__), '..', 'templates', 'poll.html'
    )
    self.response.out.write(template.render(path, template_values))

  def scan_post(self, post_id):
    logging.info('Scanning post: %s' % post_id)
    topics_found = set([])
    players = set([])
    nonexistent_players = set([])
    ignored_players = set([])
    scoring_players = set([])
    post = self.client.post(post_id).data
    if post.actor.id == BUZZ_BINGO_ID:
      return None
    post_uri = post.uri
    comments = post.comments()
    retrieved_comments = []
    post_content = post.content.lower()
    post_content = re.sub('<br />|\\r|\\n', ' ', post_content)
    # Avoid false positive
    post_content = re.sub('buzz ?bingo', 'BUZZBINGO', post_content)
    if post_content.find('BUZZBINGO') != -1:
      players.add(post.actor.id)
    for topic in models.board.TOPIC_LIST:
      if post_content.find(topic.lower()) != -1:
        topics_found.add(topic)
    if post_content.find('taco'.lower()) != -1:
      topics_found.add('taco')
    for comment in comments:
      # Need to avoid making unnecessary HTTP requests
      retrieved_comments.append(comment)
      comment_content = comment.content.lower()
      comment_content = re.sub('<br />|\\r|\\n', ' ', comment_content)
      # Avoid false positive
      comment_content = re.sub('buzz ?bingo', 'BUZZBINGO', comment_content)
      if comment_content.find('BUZZBINGO') != -1:
        players.add(comment.actor.id)
      for topic in models.board.TOPIC_LIST:
        if comment_content.find(topic.lower()) != -1:
          topics_found.add(topic)
      if comment_content.find('taco'.lower()) != -1:
        topics_found.add('taco')
    for player_id in players:
      player = models.player.Player.get_by_key_name(player_id)
      if player:
        intersection = [
          topic for topic in player.topics if topic in topics_found
        ]
        if player.has_post_scored(post_id):
          logging.info("Player already scored this.")
          # Sometimes a bingo gets missed by retrying a transaction
          db.run_in_transaction(player.verify_bingo)
        elif intersection:
          scoring_players.add(player)
          scoring_topic = random.choice(intersection)
          db.run_in_transaction(
            player.score_post, post, scoring_topic
          )
          # Can't be run in the transaction, hopefully there won't be
          # any nasty race conditions
          player.award_leader_badge()
        else:
          ignored_players.add(player)
      else:
        nonexistent_players.add(player_id)
    # Lots of logging, because this turns out to be tricky to get right.
    topics_log_message = 'Topics found:\n'
    for topic in topics_found:
      topics_log_message += topic + '\n'
    logging.info(topics_log_message)
    scoring_log_message = 'Players scoring:\n'
    for player in scoring_players:
      scoring_log_message += '%s\n' % repr(player)
    logging.info(scoring_log_message)
    ignored_log_message = 'Players ignored and not scoring:\n'
    for player in ignored_players:
      ignored_log_message += '%s\n' % repr(player)
    logging.info(ignored_log_message)
    nonexistent_log_message = 'Players who might score if they signed up:\n'
    for player_id in nonexistent_players:
      nonexistent_log_message += '%s\n' % player_id
    logging.info(nonexistent_log_message)

  def post(self):
    post_id = self.request.get('post_id')
    message = ''
    if post_id:
      self.scan_post(post_id)
    else:
      for result in self.combined_results:
        try:
          if result.actor.profile_name in PRIORITY_PROFILES:
            # Give priority access to profiles used in any demo.
            countdown = 0
            logging.info('Priority scan: %s' % result.id)
          else:
            # One second delay for everyone else, which should be fine.
            countdown = 1
          result_task = taskqueue.Task(
            name="%s-%d" % (result.id[25:], int(time.time())),
            params={
              'post_id': result.id
            },
            url='/worker/poll/',
            countdown=countdown
          )
          result_task.add()
          logging.info('Scanning task enqueued: %s' % result.id)
        except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError), e:
          logging.error(str(e))
          result_task = None
      message = 'Retrieved %d posts.' % len(self.combined_results)
    template_values = {
      'http_get': False,
      'message': message
    }
    path = os.path.join(
      os.path.dirname(__file__), '..', 'templates', 'poll.html'
    )
    self.response.out.write(template.render(path, template_values))
