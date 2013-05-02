
# NOTES
# https://github.com/michaelhelmick/python-flickr
# http://www.flickr.com/services/api/
# http://www.flickr.com/groups/api/discuss/72157600055461667/
# http://goo.gl/CvLww

import os
from pprint import pprint
import cPickle as pickle
import json
from flickr import FlickrAPI
from time import gmtime, strftime

# Open the log file
log_file_handle = open("flickr_sync_log.txt", "a")

# Cache the folder and file info
pic_folders_and_files_dict = {}
for root, dirs, files in os.walk('/home/dave/Media/Pictures'):
  pic_folders_and_files_dict[root[16:]] = files

# Get Flickr Oauth login data
flickr_session_data = pickle.load(open("flickr_session_data.p", "rb"))
my_api_key, my_api_secret, final_oauth_token, final_oauth_token_secret = flickr_session_data

# Create Flickr session class
flickr_handle = FlickrAPI(api_key=my_api_key,
  api_secret=my_api_secret,
  oauth_token=final_oauth_token,
  oauth_token_secret=final_oauth_token_secret
)

# Get the list of collections from Flickr
collections_dict = flickr_handle.get('flickr.collections.getTree')
collections_dict = collections_dict['collections']

# Put collections info into useful data structures
collections_info_dict = {}
def recursive_json_dict_walker(json_dict, so_far=""):

  # Need to handle the top-level case where there is no title field
  if ('title' in json_dict):
    so_far = so_far + "/" + json_dict['title']
    collections_info_dict[so_far] = (json_dict['id'], json_dict['set']['id'])

  if ('collection' in json_dict):
    # A collection is _always_ a list so we need to process all of them
    for list_entry in json_dict['collection']:
      recursive_json_dict_walker(list_entry, (so_far))

# Updates collections_set using recursive function
recursive_json_dict_walker(collections_dict)

# Create missing collections
for folder in sorted(pic_folders_and_files_dict.iterkeys()):
  if (folder not in collections_info_dict):
    last_slash_pos = folder.rfind('/')
    title = folder[(last_slash_pos + 1):]
    if (last_slash_pos == 0):
      parent_id = 0
    else:
      parent_string = folder[:last_slash_pos]
      parent_set_id, parent_id = collections_info_dict[parent_string]

    create_response = flickr_handle.get('flickr.collections.create', params={'title': title, 'parent_id': parent_id})
    collections_info_dict[folder] = create_response['collection']['id']
    log_string = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " : Created collection " + folder
    log_file_handle.write(log_string)

# Upload photos - create sets if required (only jpg, jpeg, gif and png)
for folder in sorted(pic_folders_and_files_dict.iterkeys()):
  for file_name in pic_folders_and_files_dict[folder]:
    print("folder: %s, file: %s" % (folder, file_name))

# Delete photos - remove sets if required

# Remove unneeded collections
for collection in sorted(collections_info_dict.iterkeys(), reverse=True):
  if collection not in pic_folders_and_files_dict:
    set_id, delete_id = collections_info_dict[collection]
    delete_response = flickr_handle.get('flickr.collections.delete', params={'collection_id': delete_id})
    del collections_info_dict[collection]
#    log_file_handle.write(log_string)



# Close log file
log_file_handle.close()

# TBD
# Log all collections, sets and photos added and removed with a timestamp
