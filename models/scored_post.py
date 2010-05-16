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

import oauth

import models.player

class ScoredPost(db.Model):
  # The player is the scored post's parent.
  post_id = db.StringProperty(required=True)
  topic = db.StringProperty(required=True)

  @property
  def player(self):
    return self.parent

  def __repr__(self):
    return "<ScoredPost[%s, %s]>" % (self.post_id, self.parent_key().name())
