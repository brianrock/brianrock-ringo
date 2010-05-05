import httplib
import buzz
import oauth

OAUTH_CONSUMER_KEY = 'buzz-bingo.appspot.com'
OAUTH_CONSUMER_SECRET = 'hW4gy8/mYfydeHA/qZT3fgEG'

http_client = httplib.HTTPConnection('www.google.com')
oauth_client = buzz.BuzzOAuthClient(http_client)
consumer = oauth.OAuthConsumer(OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET)
signature_method_plaintext = oauth.OAuthSignatureMethod_PLAINTEXT()
signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()

# UGH
oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, callback=CALLBACK_URL, http_url=client.request_token_url)
oauth_request.sign_request(signature_method_plaintext, consumer, None)
