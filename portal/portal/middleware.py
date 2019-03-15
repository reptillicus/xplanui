from django.conf import settings
import jwt
from agavepy import agave

AGAVE_RESOURCES = agave.load_resource('https://api.sd2e.org')

class PortalUser:

    def __init__(self, token):
        self.username = token["username"]
        self.access_token = token["agave_token"]["access_token"]
        self.refresh_token = token["agave_token"]["refresh_token"]
        self.created = token["agave_token"]["created"]
        self.expires = token["agave_token"]["expires_in"]

        client = agave.Agave(
            api_server='https://api.sd2e.org',
            resources=AGAVE_RESOURCES,
            token=self.access_token,
            refresh_token=self.refresh_token
        )
        self.agave_client = client

    def __repr__(self):
        return "<PortalUser {}>".format(self.access_token)

class JWTMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        tokenstr = auth_header.split()[1]
        token = jwt.decode(tokenstr, settings.SECRET_KEY)
        request.user = PortalUser(token)
        response = self.get_response(request)
        return response
