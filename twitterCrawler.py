import re, time
import graphmanager as graph
from instagram import client
from crawler import Crawler
from httplib2 import ServerNotFoundError
import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener

# constant storing the social network type
SN = 'TW'

MAX_ID_REGEX = re.compile(r'max_id=([^&]+)')
CURSOR_REGEX = re.compile(r'cursor=([^&]+)')


#####TWITTER KEYS#####
CONSUMER_KEY = 'ieZUZgZrSJJE0QLBBOsgXg'
CONSUMER_SECRET = 'PlIpSrh6unKYZISSDieBIFAB3D9f6aSh4p4Dmcn8Q'
OAUTH_TOKEN = '1015949947-0Akq5OBnEzTp7OwaIuvLNiKN6L52FNLVOW9yIyf'
OAUTH_TOKEN_SECRET = 'SJz3nXcyGt2lIKhmPiFg5VlTdHLbrRSPRRgUZ552xfe1e'
####Twitter auth handler####
auth = OAuthHandler(CONSUMER_KEY,CONSUMER_SECRET)
auth.set_access_token(OAUTH_TOKEN,OAUTH_TOKEN_SECRET)
api = tweepy.API(auth)

class twitterCrawler(Crawler):
    def __init__(self, social_network):
        super(twitterCrawler, self).__init__(social_network)

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
                time.sleep(0.7)
                user_info = api.get_user(seed_user_id)
            except ServerNotFoundError as e:
                retry = True
            retry = False
        # create first user
        user = graph.User(
            social_network=self.social_network, 
            external_id=user_info.id, 
            username=user_info.screen_name, 
            url='http://twitter.com/' + user_info.screen_name, 
            completed=False
        )
        return user

    def get_user_profile(self, user):
        '''Get user profile.'''
        # add user profile to the graph as a resource
        retry = True
        while retry:
            try:
                time.sleep(0.7)
                user_info = api.get_user(user.external_id)
                retry = False
            except ServerNotFoundError as e:
                retry = True
            except:
                return None
        if user_info.description is not None:
            raw_content = user_info.description
            if user_info.url:
                raw_content += ' ' + user_info.url

            # create user profile resource and add it to the graph
            resource = graph.Resource(
                social_network=user.social_network,
                external_id=user.external_id,
                url='http://twitter.com/' + user.username,
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
                    time.sleep(0.7) # be nice with the API
                    if max_id == '':
                        recent_media = api.user_timeline(user_id=user.external_id, count=33)
                    else:
                        recent_media = api.user_timeline(user_id=user.external_id, max_id=max_id, count=33)
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
                if hasattr(media, 'text') and media.text is not None:
                    create_resource = True
                    raw_content = media.text
                    if hasattr(media, 'place') and media.place is not None:
                        raw_content = raw_content + '. ' + media.place.name
                elif hasattr(media, 'place') and media.place is not None:
                    create_resource = True
                    raw_content = media.place

                ###NUEVO
                if media.id==max_id:
                    next=None
                else:
                    max_id=media.id
                ####
                
                if create_resource:
                    try:
                        resource = graph.Resource(
                            social_network=SN,
                            external_id=media.id,
                            url="https://twitter.com/"+media.user.screen_name+"/status/"+str(media.id),
                            raw_content=raw_content,
                            location_name=media.user.location,
                            location_lat=None,
                            location_lon=None
                        )
#,location_lat=media.location.point.latitude,
 #                           location_lon=media.location.point.longitude

                    except AttributeError:
                        resource = graph.Resource(
                            social_network=SN,
                            external_id=media.id,
                            url="https://twitter.com/"+media.user.screen_name+"/status/"+str(media.id),
                            raw_content=raw_content,
                            location_name=None,
                            location_lat=None,
                            location_lon=None
                        )
                    if resource is not None:
                        resources.append(resource)



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
                    time.sleep(0.7) # be nice with the API
                    
                    followees_page = api.get_user(user_id=user.external_id).friends(cursor=cursor)
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
            if followees_page[1][1]!=0:
                cursor+=1
            else:
                next=None
            ###
            for user_info in followees_page[0]:
                followee = graph.User(
                    social_network=SN, 
                    external_id=user_info.id, 
                    username=user_info.screen_name, 
                    url='http://twitter.com/' + user_info.screen_name,
                    completed=False
                )
                followees.append(followee)

            if next is None:
                break
            
        return followees

# let's crawl Instagram!
twitterCrawler(SN).run()
