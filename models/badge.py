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

class Badge(db.Model):
  # The player is the badge's parent.
  badge_type = db.StringProperty()
  date_awarded = db.DateTimeProperty(auto_now_add=True)
  
  @property
  def badge_icon(self):
    if self.badge_type == 'hello-world':
      return 'http://buzz-bingo.appspot.com/images/badges/helloworld.gif'
    elif self.badge_type == 'geo':
      return 'http://www.google.com/images/icons/milestone-48.png'
    elif self.badge_type == 'share':
      return 'http://www.google.com/images/icons/share-48.gif'
    elif self.badge_type == 'bingo':
      return 'http://www.google.com/images/icons/racing-48.gif'
    elif self.badge_type == 'mobile':
      return 'http://www.google.com/images/icons/mobile-48.gif'
    elif self.badge_type == 'scholar':
      return 'http://www.google.com/images/icons/scholar-48.gif'
    elif self.badge_type == 'leader':
      return 'http://www.google.com/images/icons/pegman_award-48.gif'
    elif self.badge_type == 'taco':
      return 'http://buzz-bingo.appspot.com/images/badges/taco.gif'
    else:
      raise ValueError('Unknown ')