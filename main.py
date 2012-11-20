from google.appengine.api import channel
from google.appengine.ext import deferred
import webapp2
from webapp2_extras import sessions_memcache
from webapp2_extras import sessions
from webapp2_extras import jinja2
import uuid

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(name='mc_session',
            factory=sessions_memcache.MemcacheSessionFactory)

    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        j = jinja2.get_jinja2(app=self.app)
        #        j.environment.globals['is_admin']= is_admin()
        pass
        return j

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)

class MainHandler(BaseHandler):

    def get(self):
        channel_token = self.session.get('channel_token')
        if channel_token is None: # if the session user does not have a channel token, create it and save it in the session store.
            client_id = str(uuid.uuid4()).replace("-",'')
            channel_token = channel.create_channel(client_id)
            self.session['channel_token'] = channel_token
            self.session['client_id'] = client_id

        client_id = self.session['client_id']

#put some messages in the deferred queue which will appear in the browser a few seconds after loading the page.
        deferred.defer(channel.send_message,client_id,"This is the 2 second delayed message",_countdown=2)
        deferred.defer(channel.send_message,client_id,"This is the 5 second delayed message",_countdown=5)

        self.render_response('home.html',**{"token":channel_token,"client_id":client_id})


class Send_Message(BaseHandler):
    def get(self):
        self.render_response('message.html',**{'token':self.session['channel_token'],'client_id':self.session['client_id']})

    def post(self):
        message = self.request.get("message")
       # token = self.session.get('channel_token') we don't need the token itself, just the user we're sending the message to.
        client_id = self.session['client_id']
        result = channel.send_message(client_id,message)
        self.redirect('/message')


config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': '9upj9p80pi08hn09k9jk',
}
app = webapp2.WSGIApplication([
                                   ('/', MainHandler) ,
                                   ('/message', Send_Message)
],
                             debug=True, config=config)

