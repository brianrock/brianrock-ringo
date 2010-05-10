from google.appengine.ext import webapp

class LeaderboardHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write('Hello world!')
