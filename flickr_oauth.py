
import cPickle as pickle
from flickr import FlickrAPI
from pprint import pprint

# my_api_key='33a85d0de9040f3d12ed5d17bad02210'
# my_api_secret='0a255e264884b059'

my_api_key = 'af997fbb975e9e112d3d96b64f6d3ab5'
my_api_secret = '384e545fe39b978e'

# Part 1 - get online authorisation
first_api_handle = FlickrAPI(api_key=my_api_key, api_secret=my_api_secret, callback_url='http://bowsy.me.uk/test/test.php')

auth_props = first_api_handle.get_authentication_tokens(perms='delete')
auth_url = auth_props['auth_url']

oauth_token = auth_props['oauth_token']
oauth_token_secret = auth_props['oauth_token_secret']

print 'Connect with Flickr via: %s' % auth_url

# Get final tokens
oauth_token_returned=raw_input('oauth_token_returned=')
oauth_verifier_returned=raw_input('oauth_verifier_returned=')

second_api_handle = FlickrAPI(api_key=my_api_key, 
  api_secret=my_api_secret,
  oauth_token=oauth_token,
  oauth_token_secret=oauth_token_secret
)

authorized_tokens = second_api_handle.get_auth_tokens(oauth_verifier_returned)

# Final tokens
final_oauth_token = authorized_tokens['oauth_token']
final_oauth_token_secret = authorized_tokens['oauth_token_secret']

# Pickle it!
flickr_session_data = my_api_key, my_api_secret, final_oauth_token, final_oauth_token_secret
pickle.dump(flickr_session_data, open( "flickr_session_data.p", "wb" ) )

# Show it working
third_api_handle = FlickrAPI(api_key=my_api_key,
  api_secret=my_api_secret,
  oauth_token=final_oauth_token,
  oauth_token_secret=final_oauth_token_secret
)

# THIS WORKS
# recent_activity = third_api_handle.get('flickr.activity.userComments')
# pprint(recent_activity)

# THIS DOES NOT
set_title = "Pictures_Art_Animals"
TEMP_PHOTO_ID = 8611344232
set_create_response = third_api_handle.post('flickr.photosets.create', params={'title': set_title, 'primary_photo_id ': TEMP_PHOTO_ID})
pprint(set_create_response)
