#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Discogs to iTunes script
Usage:
  {discogs2itunes} -u <username> -k <apikey> [-f <filename>] [-h] [-o] [-s]
Options:
  -f, --datafile <filename>    datafile name (optional)
  -h, --help                   show help (optional)
  -k, --apikey <api_key>       discogs api key
  -o, --override               override local values (optional)
  -s, --songs                  update itunes songs rating instead of album rating (optional)
  -u, --username <username>    discogs username
'''


import getopt
import json
import os.path
import re
import requests
import sys

from appscript import *
from datetime import datetime
from progress.bar import Bar
from time import sleep
from unidecode import unidecode


API_BASEURL = "https://api.discogs.com"
API_FORMAT = "application/vnd.discogs.v2.plaintext+json"
API_LIMIT = 100
CONVERTION_RATIO = 20
DATA_FILE = 'discogs2itunes.json'
DATE_EPOCH = datetime.utcfromtimestamp(0)
DATE_NOW = datetime.utcnow().replace(microsecond=0)


def usage():
    print(sys.exit(__doc__.format(discogs2itunes = sys.argv[0].split('/')[-1])))


def load_data(datafile):
    data = None
    if os.path.isfile(datafile):
        print("Loading file...")
        in_file = open(datafile, 'r')
        try:
            data = json.load(in_file)
        except ValueError as err:
            print("Invalid data file")
        in_file.close()
    else:
        print("Data file not found.")
    return data


def save_data(datafile, data):
    print("Writing to file...")
    out_file = open(datafile, 'w')
    try:
        json.dump(data, out_file, skipkeys=True)
    except:
        print("Unable to write to file")
    out_file.close()


def get_discogs_ratings(username, apikey, ratings={}):
    print("Fetching data from Discogs...")
    last_updated = int((DATE_NOW - DATE_EPOCH).total_seconds())
    headers = {
        'Accept':API_FORMAT,
        'Content-Type':'application/json',
        'User-Agent':'discogs2itunes' }
    query = {
        'token':apikey,
        'per_page':API_LIMIT,
        'page':1 }
    session = requests.session()
    r = session.get(API_BASEURL+'/users/'+username+'/collection/folders/0/releases', params = query, headers = headers)
    jsondoc = json.loads(r.text.encode('utf-8'))
    total_pages = int(jsondoc['pagination']['pages'])
    bar = Bar('Fetching', max=total_pages)
    for page in range(1, total_pages+1):
        query = {
            'token':apikey,
            'per_page':API_LIMIT,
            'page':page }
        r = session.get(API_BASEURL+'/users/'+username+'/collection/folders/0/releases', params = query, headers = headers)
        jsondoc = json.loads(r.text.encode('utf-8'))
        releases = jsondoc['releases']
        for release in releases:
            release_id = int(release['id'])
            release_instance_id = int(release['instance_id'])
            release_album_rating = int(release['rating'])
            release_album = unidecode(release['basic_information']['title']).encode('ascii').lower()
            release_artist = unidecode(' - '.join(map(lambda x: re.sub('\(\d+\)', '', x['name']).strip(), release['basic_information']['artists']))).encode('ascii').lower()
            #print("{0} - [{1}] {2} ({3} / {4})".format(
            #    release_artist,
            #    release_album_rating,
            #    release_album,
            #    release_id,
            #    release_instance_id ) )
            ratings.setdefault(release_artist, {})
            ratings[release_artist].setdefault(release_album, {})
            ratings[release_artist][release_album].setdefault('rating', release_album_rating)
            ratings[release_artist][release_album].setdefault('id', release_id)
            ratings[release_artist][release_album].setdefault('instance_id', release_instance_id)
        sleep(0.2)
        bar.next()
    bar.finish()
    return {'last_updated':last_updated, 'ratings':ratings}


def update_itunes_ratings(ratings, update_songs=False, override_values=False):
    print 'Updating iTunes ratings...'
    results = {
        'artists':{'miss':{}},
        'albums':{
            'miss':{},
            'updated':{},
            'not_updated':{} },
        'songs':{
            'miss':{},
            'updated':{},
            'not_updated':{} } }
    itunes = app('iTunes')
    library = itunes.library_playlists['Library']
    tracks = library.tracks()
    bar = Bar('Updating', max=len(tracks))
    for track in tracks:
        track_artist = unidecode(track.artist()).encode('ascii').lower()
        track_album = unidecode(track.album()).encode('ascii').lower()
        track_name = unidecode(track.name()).encode('ascii').lower()
        track_album_rating = int(track.album_rating())
        track_rating = int(track.rating())
        discogs_artist = ratings.get(track_artist, None)
        if discogs_artist is None:
            # artist not in discogs
            results['artists']['miss'].setdefault(track_artist, 1)
            bar.next()
            continue
        discogs_album = ratings[track_artist].get(track_album, None)
        if discogs_album is None:
            # album not yet in discogs
            results['albums']['miss'].setdefault(track_artist, {})
            results['albums']['miss'][track_artist].setdefault(track_album, 1)
            results['songs']['miss'].setdefault(track_artist, {})
            results['songs']['miss'][track_artist].setdefault(track_name, 0)
            results['songs']['miss'][track_artist][track_name] += 1
            bar.next()
            continue
        discogs_rating = discogs_album['rating'] * CONVERTION_RATIO
        if update_songs:
            # update song
            if discogs_rating > track_rating or override_values:
                # song rating updated
                results['songs']['updated'].setdefault(track_artist, {})
                results['songs']['updated'][track_artist].setdefault(track_name, {'from':track_album_rating, 'to':discogs_rating})
                track.rating.set(discogs_rating)
            else:
                # song rating not updated
                results['songs']['not_updated'].setdefault(track_artist, {})
                results['songs']['not_updated'][track_artist].setdefault(track_name, {'from':track_album_rating, 'to':discogs_rating})
        else:
            # update album
            if discogs_rating > track_album_rating or override_values:
                results['albums']['updated'].setdefault(track_artist, {})
                results['albums']['updated'][track_artist].setdefault(track_album, {'from':track_album_rating, 'to':discogs_rating})
                track.album_rating.set(discogs_rating)
            else:
                # rating not updated
                results['albums']['not_updated'].setdefault(track_artist, {})
                results['albums']['not_updated'][track_artist].setdefault(track_album, {'from':track_album_rating, 'to':discogs_rating})
        #print("{0} - [{1} -> {2}] {3} - [{4} -> {5}] {6}".format(
        #    track_artist.encode('utf-8'),
        #    track_album_rating,
        #    discogs_rating,
        #    track_album.encode('utf-8'),
        #    track_rating,
        #    discogs_rating,
        #    track_name.encode('utf-8') )
        bar.next()
    bar.finish()
    #print(results)
    artists_miss = reduce(lambda x,y: x+y, results['artists']['miss'].values() or [0])
    albums_miss = reduce(lambda x,y: x+y, map(lambda x: reduce(lambda x,y: x+y, x.values()), results['albums']['miss'].values()) or [0])
    albums_updated = reduce(lambda x,y: x+y, map(lambda x: len(x.keys()), results['albums']['updated'].values()) or [0])
    albums_not_updated = reduce(lambda x,y: x+y, map(lambda x: len(x.keys()), results['albums']['not_updated'].values()) or [0])
    songs_miss = reduce(lambda x,y: x+y, map(lambda x: reduce(lambda x,y: x+y, x.values()), results['songs']['miss'].values()) or [0])
    songs_updated = reduce(lambda x,y: x+y, map(lambda x: len(x.keys()), results['songs']['updated'].values()) or [0])
    songs_not_updated = reduce(lambda x,y: x+y, map(lambda x: len(x.keys()), results['songs']['not_updated'].values()) or [0])
    print("{} band misses".format(artists_miss))
    print("{} album misses".format(albums_miss))
    print("{} albums updated".format(albums_updated))
    print("{} albums not updated".format(albums_not_updated))
    print("{} song misses".format(songs_miss))
    print("{} songs updated".format(songs_updated))
    print("{} songs not updated".format(songs_not_updated))


def main(argv):
    username = None
    apikey = None
    datafile = DATA_FILE
    last_updated = 0
    override_values = False
    ratings = {}
    update_songs = False
    try:
        opts, args = getopt.getopt(argv, "hu:k:f:so", ["help", "username=", "apikey=", "datafile=" "songs", "override"])
    except getopt.GetoptError as err:
        sys.exit("  " + str(err))
    if not opts:
        usage()
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-u', '--username'):
            username = arg
        elif opt in ('-k', '--apikey'):
            apikey = arg
        elif opt in ('-f', '--datafile'):
            datafile = arg
        elif opt in ('-s', '--songs'):
            update_songs = True
        elif opt in ('-o', '--override'):
            override_values = True
    if not username or not apikey:
        sys.exit(str("  'username' and 'apikey' are mandatory"))
    data = load_data(datafile)
    if data:
        last_updated = data.get('last_updated', 0)
        ratings = data.get('ratings', {})
    data = get_discogs_ratings(username, apikey, ratings)
    save_data(datafile, data)
    update_itunes_ratings(data['ratings'], update_songs, override_values)


if __name__ == "__main__":
    main(sys.argv[1:])
