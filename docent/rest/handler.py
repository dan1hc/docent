import docent.core

import http.server
import json
import urllib.parse

from . import constants
from . import objects
from . import resource
from . import route


class Constants(constants.FrameworkConstants):  # noqa

    pass


class DocHandler(http.server.BaseHTTPRequestHandler):  # noqa

    def log_message(*args, **kwargs):  # noqa
        pass

    def respond(
        self,
        response: objects.response.Response
        ):  # noqa
        self.send_response(response.status_code)
        for header, value in response._headers.items():
            self.send_header(header, str(value))
        self.end_headers()
        if response._encoded:
            self.wfile.write(response._content)
        else:
            self.wfile.write(response._content.encode())

    def get_request(self) -> objects.Request:  # noqa
        parsed = urllib.parse.urlparse(self.path)
        path_as_list = [
            s
            for s
            in parsed.path.strip('/').split('/')
            if s
            ]

        docent.core.log.debug(
            {
                'resource': 'DocHandler',
                'message': 'handling request',
                'path': parsed.path.strip('/'),
                'path_as_list': path_as_list,
                },
            )

        rsc = None
        if path_as_list and any(
            (
                path_as_list[-1].endswith('.ico'),
                path_as_list[-1].endswith('.json'),
                path_as_list[-1].endswith('.png'),
                path_as_list[-1].endswith('.yaml'),
                path_as_list[-1].startswith('docs'),
                )
            ):
            rsc = objects.documentation.Swagger
            path_parameters = {}
        else:
            for resource_meta in route.Route.APPLICATION_RESOURCES:
                if (
                    resource_meta[0] == 'healthz'
                    and not path_as_list
                    ):
                    path_trimmed = 'healthz'
                elif len(path_as_list) > (
                    len(s := resource_meta[0].split('/'))
                    + len(resource_meta[1])
                    + 1
                    ):
                    continue
                elif len(path_as_list) < (
                    len(s := resource_meta[0].split('/'))
                    + len(resource_meta[1])
                    ):
                    continue
                else:
                    path_trimmed = '/'.join(
                        [
                            v
                            for i, v
                            in enumerate(path_as_list)
                            if (
                                i not in resource_meta[1]
                                and i < len(s)
                                )
                            ]
                        )

                if resource_meta[0] == path_trimmed:
                    rsc: resource.Resource = resource_meta[2]
                    path_key = rsc.validate_path(path_as_list)
                    path_obj = rsc.PATHS[
                        '.'.join((rsc.__module__, rsc.__name__))
                        ][path_key]
                    path_ref_as_list = path_obj._name.split('/')
                    path_parameters = {
                        path_ref_as_list[i][1:-1]: v
                        for i, v
                        in enumerate(path_as_list)
                        if (
                            i in resource_meta[1]
                            or (
                                i >= len(resource_meta[0].split('/'))
                                and path_key == 'ID'
                                and self.command != 'POST'
                                )
                            )
                        }
                    break

        if rsc is None:
            return

        query_parameters = {
            urllib.parse.unquote(s[0]): urllib.parse.unquote(s[1])
            for _s
            in parsed.query.split('&')
            if (s := _s.split('='))
            and len(s) == 2
            }

        if (content := self.headers.get('Content-Length')):
            if (
                data := self.rfile.read(int(content)).decode(errors='replace')
                ):
                body = json.loads(data)
            else:
                body = {}
        else:
            body = None

        return objects.Request(
            body=body,
            headers=dict(self.headers),
            method=self.command,
            path=parsed.path,
            params={
                **path_parameters,
                **query_parameters,
                },
            )

    def do_DELETE(self):  # noqa
        if (request := self.get_request()):
            response_obj, status_code = route.Route[request]
        else:
            err = (
                objects
                .response
                .Error
                .from_exception(FileNotFoundError)
                )
            response_obj, status_code = err, err.errorCode
        response = objects.response.Response(
            body=response_obj,
            status_code=status_code,
            )
        self.respond(response)

    def do_GET(self):  # noqa
        if (request := self.get_request()):
            response_obj, status_code = route.Route[request]
        else:
            err = (
                objects
                .response
                .Error
                .from_exception(FileNotFoundError)
                )
            response_obj, status_code = err, err.errorCode
        response = objects.response.Response(
            body=response_obj,
            status_code=status_code,
            )
        self.respond(response)

    def do_OPTIONS(self):  # noqa
        if (request := self.get_request()):
            response_obj, status_code = route.Route[request]
        else:
            err = (
                objects
                .response
                .Error
                .from_exception(FileNotFoundError)
                )
            response_obj, status_code = err, err.errorCode
        response = objects.response.Response(
            body=response_obj,
            status_code=status_code,
            )
        self.respond(response)

    def do_PATCH(self):  # noqa
        if (request := self.get_request()):
            response_obj, status_code = route.Route[request]
        else:
            err = (
                objects
                .response
                .Error
                .from_exception(FileNotFoundError)
                )
            response_obj, status_code = err, err.errorCode
        response = objects.response.Response(
            body=response_obj,
            status_code=status_code,
            )
        self.respond(response)

    def do_POST(self):  # noqa
        if (request := self.get_request()):
            response_obj, status_code = route.Route[request]
        else:
            err = (
                objects
                .response
                .Error
                .from_exception(FileNotFoundError)
                )
            response_obj, status_code = err, err.errorCode
        response = objects.response.Response(
            body=response_obj,
            status_code=status_code,
            )
        self.respond(response)

    def do_PUT(self):  # noqa
        if (request := self.get_request()):
            response_obj, status_code = route.Route[request]
        else:
            err = (
                objects
                .response
                .Error
                .from_exception(FileNotFoundError)
                )
            response_obj, status_code = err, err.errorCode
        response = objects.response.Response(
            body=response_obj,
            status_code=status_code,
            )
        self.respond(response)
