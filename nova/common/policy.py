# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 OpenStack, LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Common Policy Engine Implementation"""

import json
import urllib
import urllib2


def NotAllowed(Exception):
    pass


def enforce(match_list, target_dict, credentials_dict):
  """Check the authz of some rules against credentials.

  Match lists look like:

    ('rule:compute:get_volume',)

  or

    (('role:compute_admin',),
     ('tenant_id:%(tenant_id)s', 'role:compute_sysadmin'))


  Target dicts contain as much information as we can about the object being
  operated on.

  Credentials dicts contain as much information as we can about the user
  performing the action.

  """
  b = Brain()
  if not b.check(match_list, target_dict, credentials_dict):
    raise NotAllowed()


class Brain(object):
  # class level on purpose, the brain is global
  rules = {}

  def __init__(self, rules=None):
    if rules is not None:
      self.__class__.rules = rules

  def add_rule(self, key, match):
    self.rules[key] = match

  def check(self, match_list, target_dict, cred_dict):
    for and_list in match_list:
      matched = False
      for match in and_list:
        match_kind, match = match.split(':', 2)
        if hasattr(self, '_check_%s' % match_kind):
          f = getattr(self, '_check_%s' % match_kind)
          rv = f(match, target_dict, cred_dict)
          if not rv:
            matched = False
            break
        else:
          rv = self._check(match, target_dict, cred_dict)
          if not rv:
            matched = False
            break
        matched = True

      # all AND matches passed
      if matched:
        return True

    # no OR rules matched
    return False

  def _check_rule(self, match, target_dict, cred_dict):
    new_match_list = self.rules.get(match[5:])
    return self.check(new_match_list, target_dict, cred_dict)

  def _check_generic(self, match, target_dict, cred_dict):
    """Check an individual match.

    Matches look like:

      tenant:%(tenant_id)s
      role:compute:admin

    """

    # TODO(termie): do dict inspection via dot syntax
    match = match % target_dict
    key, value = match.split(':', 2)
    if key in cred_dict:
      return value == cred_dict[key]
    return False


class HttpBrain(object):
  """A brain that can check external urls a

  Posts json blobs for target and credentials.

  """

  def _check_http(self, match, target_dict, cred_dict):
    url = match % target_dict
    data = {'target': json.dumps(target_dict),
            'credentials': json.dumps(cred_dict)}
    post_data = urllib.urlencode(data)
    f = urllib2.urlopen(url, post_data)
    if f.read():
      return True
    return False


def load_json(path):
  rules_dict = json.load(open(path))
  b = Brain(rules=rules_dict)
