from google.appengine.ext import webapp

class PlayHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write('Hello world!')
