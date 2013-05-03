
# NOTES
# https://github.com/michaelhelmick/python-flickr
# http://www.flickr.com/services/api/
# http://www.flickr.com/groups/api/discuss/72157600055461667/
# http://goo.gl/CvLww

import os
from pprint import pprint
import cPickle as pickle
import json
from flickr import FlickrAPI, FlickrAPIError
from time import gmtime, strftime
import logging

# For debugging
import pdb

# Constants
temp_photo_id = '8611344232'
pic_folder_location = '/home/dave/Media/'

# Function to check if photo should be uploaded
def valid_photo(photo_name):
  p_n_l = photo_name.lower()
  if (p_n_l.endswith('jpg') or p_n_l.endswith('jpeg') or p_n_l.endswith('gif') or p_n_l.endswith('bmp') or p_n_l.endswith('png')):
    return True
  else:
    return False

# Function to output to the log
def log_string(output):
  log_string = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " : " + output
  logging.info(log_string)

# Set up logging
logging.basicConfig(filename='/home/dave/Development/Flickr-Sync/flickr_sync_log.txt',level=logging.DEBUG)
log_string(">>> RESTART <<<")

# Cache the folder and file info
pic_folders_array = {}
for root, dirs, files in os.walk('/home/dave/Media/Pictures'):
  pic_folders_array[root[16:]] = files

# Get Flickr Oauth login data
flickr_session_data = pickle.load(open("flickr_session_data.p", "rb"))
my_api_key, my_api_secret, final_oauth_token, final_oauth_token_secret = flickr_session_data

# Set up error handling
try:

  # Create Flickr session instance
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
      collections_info_dict[so_far] = (json_dict['id'])
    if ('collection' in json_dict):
      # A collection is _always_ a list so we need to process all of them
      for list_entry in json_dict['collection']:
        recursive_json_dict_walker(list_entry, (so_far))

  # Update collections_set using recursive function
  recursive_json_dict_walker(collections_dict)

  # Create missing collections and their leaf-node sets
  for folder in sorted(pic_folders_array.iterkeys()):
    parent_id = 0
    if (folder not in collections_info_dict):
      last_slash_pos = folder.rfind('/')
      collection_title = folder[(last_slash_pos + 1):]
      if (last_slash_pos != 0):
        parent_string = folder[:last_slash_pos]
        parent_id = collections_info_dict[parent_string]

      # Call create collection API
      collection_create_response = flickr_handle.get('flickr.collections.create', params={'title': collection_title, 'parent_id': parent_id})
      # Add newly created collection into local data cache
      new_collection_id = collection_create_response['collection']['id']
      collections_info_dict[folder] = new_collection_id
      # Log newly created collection
      log_string("Created collection " + collection_title)
      # Now we need to create a new set using the temporary photo as primary picture but only if it's a leaf node folder
      full_folder = pic_folder_location + folder
      dirs = [d for d in os.listdir(full_folder) if os.path.isdir(os.path.join(full_folder, d))]
      if (len(dirs) == 0):
        setCreated = True
        set_title = folder.replace('/', '_')[1:]
        set_create_response = flickr_handle.get('flickr.photosets.create', params={'title': set_title, 'primary_photo_id': temp_photo_id})
        new_set_id = set_create_response['photoset']['id']
        # Log set creation
        log_string("Created set " + set_title)
        # Add set to collection
        adding_response = flickr_handle.get('flickr.collections.editSets', params={'collection_id': new_collection_id, 'photoset_ids': new_set_id})
        setCreated = False
        # Log added set to collection
        log_string("Added set " + set_title + " to collection " + collection_title)

  # Get all the photosets
  set_list_response = flickr_handle.get('flickr.photosets.getList');
  set_list_response = set_list_response['photosets']['photoset']
  # For each photoset
  for set_entry in set_list_response:
    # Get the list of photos in the local folder
    set_title = set_entry['title']['_content']
    folder_name = "/" + set_title.replace('_', '/')
    files_in_folder = pic_folders_array[folder_name]
    # Get list of all photos in photoset
    set_id = set_entry['id']
    get_photos_response = flickr_handle.get('flickr.photosets.getPhotos', params={'photoset_id': set_id})
    get_photos_response = get_photos_response['photoset']['photo']
    # For every photo in the folder
    first_upload = True
    for local_photo in files_in_folder:
      # Check it's something we can upload
      if (valid_photo(local_photo)):
        # Now check it's not already up there - first time off the extension
        dot_pos = local_photo.rfind(".")
        local_photo_trimmed = local_photo[:dot_pos]
        photo_found = False
        for photo_entry in get_photos_response:
          photo_id = photo_entry['id']
          if (local_photo_trimmed == photo_entry['title']):
            photo_found = True
            continue
        if (not photo_found):
          # Upload it
          photo_to_upload = open(pic_folder_location + folder_name + "/" + local_photo, 'rb')
          added_photo_response = flickr_handle.post(params={'title': local_photo_trimmed}, files=photo_to_upload)
          added_photo_id = added_photo_response['photoid']
          # Log uploading
          log_string("Uploaded photo " + local_photo)
          # Add uploaded photo to set
          add_to_set_response = flickr_handle.get('flickr.photosets.addPhoto', params={'photoset_id': set_id, 'photo_id': added_photo_id})
          # Log adding to set
          log_string("Added photo " + local_photo + " to set " + set_title)
          # If it's the first upload into this set this session see if we need to 
          # set new primary photo and remove temporary one
          if (first_upload):
            first_upload = False
            for test_photo_entry in get_photos_response:
              if (test_photo_entry['id'] == temp_photo_id):
                set_primary_response = flickr_handle.get('flickr.photosets.setPrimaryPhoto', params={'photoset_id': set_id, 'photo_id': added_photo_id})
                # Log setting new primary photo
                log_string("Set new primary photo for " + set_title + " to " + local_photo)
                remove_photo_from_set_response = flickr_handle.get('flickr.photosets.removePhoto', params={'photoset_id': set_id, 'photo_id': temp_photo_id})
                # Log removing temporary photo from set
                log_string("Removing temporary photo from " + set_title)
                break

except FlickrAPIError, e:
  log_string("Exception caught!")
  log_string(e.msg)
  log_string(e.code)
