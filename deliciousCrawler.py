import re, time
import graphmanager as graph
from instagram import client
from crawler import Crawler
from httplib2 import ServerNotFoundError
import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import deliciousapi
import json

# constant storing the social network type
SN = 'DL'

MAX_ID_REGEX = re.compile(r'max_id=([^&]+)')
CURSOR_REGEX = re.compile(r'cursor=([^&]+)')

api = deliciousapi.DeliciousAPI()
url = "http://www.michael-noll.com/wiki/Del.icio.us_Python_API"
username = "bob"


class deliciousCrawler(Crawler):
    def __init__(self, social_network):
        super(deliciousCrawler, self).__init__(social_network)

    def get_first_user(self):
        '''Get the first user to init the graph.'''
        # entry point to the graph: a user named smhopeless
        # this guy is a music producer from pamplona
        seed_user_id = 79708782
        # create first user and add him to the graph
        # get user info from Instagram
        retry = True
        while retry:
            try:
                time.sleep(1)
                user_info = api.get_user(username)
                retry = False
            except ServerNotFoundError as e:
                retry = True
            
        # create first user
        user = graph.User(
            social_network=self.social_network, 
            external_id=0, 
            username=user_info.username, 
            url='https://delicious.com/' + user_info.username, 
            completed=False
        )
        return user

    def get_user_profile(self, user):
        #'''Get user profile.'''
        # add user profile to the graph as a resource
        retry = True
        while retry:
            try:
                time.sleep(1)
                user_info = api.get_user(user.username)
                retry = False
            except ServerNotFoundError as e:
                retry = True
            except:
                return None
        if user_info.username is not None:
            raw_content = user_info.username
            if user_info.username:
                raw_content += ' ' + 'https://delicious.com/' + user_info.username

            # create user profile resource and add it to the graph
            resource = graph.Resource(
                social_network=user.social_network,
                external_id=str(0),
                url='https://delicious.com/' + user_info.username,
                raw_content=raw_content,
                location_name=None,
                location_lat=None,
                location_lon=None
            )
            return resource
        else:
            return None

    def get_user_resources(self, user):
        '''Get resources from the user.'''
        resources = []
        max_id = ''
        while True:
            followees_page = []
            next = ''
            retry = True
            error = False
            while retry:
                try:
                    time.sleep(1) # be nice with the API
                    if max_id == '':
                        recent_media = api.get_user(user.username,max_bookmarks=100).bookmarks
                    else:
                        recent_media = api.get_user(user.username,max_bookmarks=100).bookmarks
                    retry = False
                except ServerNotFoundError as e:
                    retry = True
                except:
                    error = True
                    break;

            if error:
                break;

            for media in recent_media:
                create_resource = False
                if len(media)>=4 and media[3] is not None:
                    create_resource = True
                    raw_content = media[3]
                    if media[1] is not None:
                        raw_content = raw_content + '. ' + str(media[1])
                elif media[1] is not None:
                    create_resource = True
                    raw_content = str(media[1])
              
                if create_resource:
                    try:
                        resource = graph.Resource(
                            social_network=SN,
                            external_id=str(0),
                            url=media[0],
                            raw_content=raw_content,
                            location_name=None,
                            location_lat=None,
                            location_lon=None
                        )
#,location_lat=media.location.point.latitude,
 #                           location_lon=media.location.point.longitude

                    except AttributeError:
                        resource = graph.Resource(
                            social_network=SN,
                            external_id=str(0),
                            url=media[0],
                            raw_content=raw_content,
                            location_name=None,
                            location_lat=None,
                            location_lon=None
                        )
                    if resource is not None:
                        resources.append(resource)


            next=None            
            if next is None:
                break
            """else:
                # get max_id param for the next page of results
                max_id_matcher = MAX_ID_REGEX.search(next)
                if max_id_matcher is not None:
                    max_id = max_id_matcher.group(1)
                else:
                    break"""
        return resources

    def get_user_followees(self, user):
        '''Get all people that this user follows.'''
        followees = []
        cursor = -1

        while True:
            followees_page = []
            next = ''
            retry = True
            error = False
            while retry:
                try:
                    time.sleep(1) # be nice with the API
                    url="http://feeds.delicious.com/v2/json/networkmembers/"+username
                    followees_page = json.loads(urllib2.urlopen(url))

                    retry = False
                except ServerNotFoundError as e:
                    retry = True
                except:
                    error = True
                    break;

            if error:
                break;
            ###Nuevo
            #>>> us.friends(cursor=-1)[1]
            #(0, 1460009616470583290L) si el segundo campo sale 0 es que no hay mas paginas
            
            for user_info in followees_page:
                followee = graph.User(
                    social_network=SN, 
                    external_id=0, 
                    username=user_info['user'], 
                    url='https://delicious.com/'+user_info['user'],
                    completed=False
                )
                followees.append(followee)
            next=None
            if next is None:
                break
            
        return followees

# let's crawl Instagram!
deliciousCrawler(SN).run()


"""
>>> url="http://feeds.delicious.com/v2/json/userinfo/"+username
>>> import urllib2
>>> response=urllib2.urlopen(url)
>>> res=response.read()
>>> res
'[{"n": 1931, "d": "Items", "id": "items"}, {"n": 5, "d": "Network Members", "id": "networkmembers"}, {"n": 49, "d": "Network Fans", "id": "networkfans"}]'
>>> 
"""
