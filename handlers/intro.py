import os.path
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class IntroHandler(webapp.RequestHandler):
  def get(self):
    template_values = {}
    template_path = os.path.join(
      os.path.dirname(__file__), '..', 'templates', 'intro.html'
    )
    self.response.out.write(template.render(template_path, template_values))
