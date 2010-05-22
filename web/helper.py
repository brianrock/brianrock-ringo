import logging
import time

def cookie_expiration_date():
  # Expires in one month
  expiration = time.gmtime(time.time() + 2628000)
  return time.strftime("%a, %d %b %Y %H:%M:%S GMT", expiration)

def set_request_token_cookie(handler, oauth_request_token):
  handler.response.headers._headers.append((
    'Set-Cookie',
    'request_token=' + oauth_request_token.key + '; ' + \
    'path=/; expires=' + cookie_expiration_date()
  ))
  
def set_access_token_cookie(handler, oauth_access_token):
  handler.response.headers._headers.append((
    'Set-Cookie',
    'access_token=' + oauth_access_token.key + '; ' + \
    'path=/; expires=' + cookie_expiration_date()
  ))
  handler.response.headers._headers.append((
    'Set-Cookie',
    'request_token=_; ' + \
    'path=/; expires=Fri, 31-Dec-1980 23:59:59 GMT'
  ))
  
def clear_oauth_token_cookies(handler):
  handler.response.headers._headers.append((
    'Set-Cookie',
    'request_token=_; ' + \
    'path=/; expires=Fri, 31-Dec-1980 23:59:59 GMT'    
  ))
  handler.response.headers._headers.append((
    'Set-Cookie',
    'access_token=_; ' + \
    'path=/; expires=Fri, 31-Dec-1980 23:59:59 GMT'    
  ))
  
def parse_cookies(handler):
  cookies = {}
  if handler.request.headers.get('Cookie'):
    cookie_list = handler.request.headers.get('Cookie').split(';')
    for cookie in cookie_list:
      if '=' in cookie:
        k, v = cookie.strip().split('=', 1)
        cookies[k] = v.strip()
      else:
        cookies[cookie] = None
        logging.warning('Cookie with no value set: \'%s\'' % cookie)
  return cookies
