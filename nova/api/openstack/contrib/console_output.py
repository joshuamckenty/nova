# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
# Copyright 2011 Grid Dynamics
# Copyright 2011 Eldar Nugaev, Kirill Shileev, Ilya Alekseyev
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
#    under the License

import webob

from nova import compute
from nova import exception
from nova import log as logging
from nova.api.openstack import extensions


LOG = logging.getLogger('nova.api.openstack.contrib.console_output')


class Console_output(extensions.ExtensionDescriptor):

    def __init__(self):
        self.compute_api = compute.API()
        super(Console_output, self).__init__()

    def get_console_output(self, input_dict, req, server_id):
        """Get text console output."""
        context = req.environ['nova.context']
        length = input_dict['getConsoleOutput'].get('length')
        try:
            if length:
                return '\n'.join(self.compute_api.get_console_output(context, 
                                 server_id).split('\n')[-int(length):])
            else:
                return self.compute_api.get_console_output(context, server_id)
        except exception.ApiError, e:
            raise webob.exc.HTTPBadRequest(explanation=e.message)
        except exception.NotAuthorized, e:
            raise webob.exc.HTTPUnauthorized()

        return webob.Response(status_int=202)

    def get_name(self):
        return "Console_output"

    def get_alias(self):
        return "os-console-output"

    def get_description(self):
        return "Instance Console Output (text console output support)"

    def get_namespace(self):
        return "http://docs.openstack.org/ext/os-console-output/api/v1.1"

    def get_updated(self):
        return "2011-10-21T00:00:00+00:00"

    def get_resources(self):
        resources = []

        res = extensions.ResourceExtension('os-console-output',
                         Console_output(),
                         member_actions={})
        resources.append(res)

        return resources

    def get_actions(self):
        """Return the actions the extension adds, as required by contract."""
        actions = [extensions.ActionExtension("servers", "getConsoleOutput",
                                              self.get_console_output),]

        return actions
