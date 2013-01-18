#!/usr/bin/env python
#
# Copyright 2011 HubSpot Inc. All Rights Reserved.
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

__author__ = "markitecht (Christopher O'Donnell)"

import re
import hmac
import base64
import urllib
import httplib
import logging
from xml.dom import minidom

HEALTHGRAPH_API_BASE = 'api.runkeeper.com'
HEALTHGRAPH_AUTH_URL = 'https://runkeeper.com/apps/authorize'
HEALTHGRAPG_TOKEN_URL = 'https://runkeeper.com/apps/token'

try:
  import hashlib
except ImportError:
  import md5 as hashlib

try:
  import json as simplejson
  simplejson.loads
except (ImportError, AttributeError):
  try:
    import simplejson
    simplejson.loads
  except (ImportError, AttributeError):
    try:
      from django.utils import simplejson
      simplejson.loads
    except (ImportError, AttributeError):
      try:
        import jsonlib as simplejson
        simplejson.loads
      except:
        pass


class HealthGraphClient(object):
  '''Client for interacting with the Health Graph APIs'''
  
  def __init__(self, access_token):
    self.access_token = access_token
  
  def _create_path(self, method):
    pass
  
  def _http_error(self, code, message, url):
    logging.error('Client request error. Code: %s - Reason: %s // %s - URL: %s' % (str(code), message['message'], message['detail'], url))
  
  def _prepare_response(self, code, data):
    if data:
      try:
        data = simplejson.loads(data)
      except ValueError:  
        pass
    return data
  
  def _get_msg(self, code):
    messages = {
      '200': {'message': 'OK', 'detail':	'Success!'},
      '304': {'message': 'Not Modified', 'detail':	'The requested resource has not been modified since the time included in the If-Modified-Since request header.'},
      '400': {'message': 'Bad Request', 'detail':	'The request could not be understood due to malformed syntax.'},
      '401': {'message': 'Unauthorized', 'detail':	'Authentication credentials were missing or incorrect.'},
      '403': {'message': 'Forbidden', 'detail':	'The request is understood but it has been refused, either due to insufficient permission or to a rate limit violation.'},
      '404': {'message': 'Not Found', 'detail':	'The URI requested is invalid or the resource requested, such as a user, does not exist.'},
      '405': {'message': 'Method Not Allowed', 'detail':	'The URI requested does not support the specific HTTP method used in the request.'},
      '406': {'message': 'Not Acceptable', 'detail':	'The URI requested does not support any of the MIME types given in the Accept header.'},
      '415': {'message': 'Unsupported Media Type', 'detail':	'The URI requested cannot accept the MIME type given in the Content-Type header.'},
      '500': {'message': 'Internal Server Error', 'detail':	'Something is broken. Please contact support so the RunKeeper team can investigate.'},
      '502': {'message': 'Bad Gateway', 'detail':	'RunKeeper is down or being upgraded.'},
      '503': {'message': 'Service Unavailable', 'detail':	'The RunKeeper servers are up, but overloaded with requests. Try again later.'}
    }
    
    return messages[code]
  
  def _deal_with_content_type(self, output):
    if output == "atom" or output == "xml":
      return "atom+xml"
    return "json"
  
  def make_request(self, resource, content_type='application/json; charset=utf-8', media_type=None, data=None, request_method='GET', url=None):

    client = httplib.HTTPSConnection(HEALTHGRAPH_API_BASE)
    
    if data and not isinstance(data, str):
      data = urllib.urlencode(data)
    
    if url is None:
      url = resource
    
    headers = {
      'Content-Type': content_type,
      'Authorization': 'Bearer %s' % self.access_token,      
      'Accept-Charset': 'UTF-8'
    }
    
    if media_type:
      headers['Accept'] = media_type
      
    client.request(request_method, url, data, headers)
    result = client.getresponse()
    if result.status < 400:
      body = result.read()
      client.close()
      if body:
        return self._prepare_response(result.status, body)
      else:
        return self._prepare_response(result.status, None)
    else:
      client.close()
      self._http_error(result.status, result.reason, url)
      return self._prepare_response(result.status, {})
  
  def get_user(self, user_id):
    media_type = 'application/vnd.com.runkeeper.User+json'
    return self.make_request('/user', media_type = media_type)
