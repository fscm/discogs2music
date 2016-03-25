#!/usr/bin/python
#
# -*- coding: utf-8 -*-
# coding: UTF-8
# encoding: utf-8
#

'''\nDiscogs to iTunes script
Usage: 
  discogs2itunes.py -u <username> -k <apikey> [-s -f <filename>]
Options:
  --help, -h                   show help
  --apikey, -k <api_key>       discogs api key
  --username, -u <username>    discogs username
  --songs, -s                  update itunes songs rating instead of album rating
  --datafile, -f <filename>    datafile name (optional)
'''


import getopt
import inflection
import json
import marshal
import os.path
import re
import requests
import sys

from appscript import *
from progress.bar import Bar
from time import sleep


api_accept = 'application/vnd.discogs.v2.plaintext+json'
api_baseurl = 'https://api.discogs.com'
api_limit = 100
data_file = 'discogs2itunes.dat'
convertion_ratio = 20


def usage():
    print sys.exit(__doc__)


def get_discogs_ratings(username, apikey):
    print "Geting Discogs ratings..."
    ratings = {}
    headers =  {'Accept':api_accept, 'Content-Type':'application/json', 'User-Agent':'discogs2itunes'}
    query = {'token':apikey, 'per_page':api_limit, 'page':1}
    session = requests.session()
    r = session.get(api_baseurl+'/users/'+username+'/collection/folders/0/releases', params = query, headers = headers)
    jsondoc = json.loads(r.text.encode('utf-8'))
    total_pages = int(jsondoc['pagination']['pages'])
    bar = Bar('Fetching', max=total_pages)
    for page in range(total_pages):
        query = {'token':apikey, 'per_page':api_limit, 'page':page}
        r = session.get("%s/users/%s/collection/folders/0/releases" % (api_baseurl, username), params = query, headers = headers)
        jsondoc = json.loads(r.text.encode('utf-8'))
        releases = jsondoc['releases']
        for release in releases:
            release_id = int(release['id'])
            release_instance_id = int(release['instance_id'])
            release_album_rating = int(release['rating'])
            release_album = str(inflection.parameterize(release['basic_information']['title'].lower()))
            release_artist = str(inflection.parameterize(' - '.join(map(lambda x: re.sub('\(\d+\)', '', x['name']).strip(), release['basic_information']['artists'])).lower()))
            ## print "%s - [%i] %s (%i / %i)" % (release_artist, release_album_rating, release_album, release_id, release_instance_id)
            ratings.setdefault(release_artist, {})
            ratings[release_artist].setdefault(release_album, {})
            ratings[release_artist][release_album].setdefault('rating', release_album_rating)
            ratings[release_artist][release_album].setdefault('id', release_id)
            ratings[release_artist][release_album].setdefault('instance_id', release_instance_id)
        sleep(0.25)
        bar.next()
    bar.finish()
    return ratings


def load_data(datafile):
    data = None
    if os.path.isfile(datafile):
        print "Loading file..."
        in_file = open(datafile, 'rb')
        data = marshal.load(in_file)
        in_file.close()
    else:
        print "Data file not found."
    return data


def save_data(datafile, data):
    print "Writing to file..."
    out_file = open(datafile, 'wb')
    marshal.dump(data, out_file)
    out_file.close()


def update_itunes_ratings(discogs_ratings, update_songs=False):
    print 'Updating iTunes ratings...'
    results = {'artists':{'miss':{}}, 'albums':{'miss':{}, 'updated':{}, 'not_updated':{}}, 'songs':{'miss':{}, 'updated':{}, 'not_updated':{}}}
    itunes = app('iTunes')
    library = itunes.library_playlists['Library']
    tracks = library.file_tracks()
    bar = Bar('Updating', max=len(tracks))
    for track in tracks:
        track_artist = str(inflection.parameterize(track.artist().lower()))
        track_album = str(inflection.parameterize(track.album().lower()))
        track_name = str(inflection.parameterize(track.name().lower()))
        track_album_rating = int(track.album_rating())
        track_rating = int(track.rating())
        ## print "%s - [%i] %s - [%i] %s" % (track_artist, track_album_rating, track_album, track_rating, track_name)
        discogs_artist = discogs_ratings.get(track_artist, None)
        if discogs_artist is None:
            # artist not in discogs
            results['artists']['miss'].setdefault(track_artist, 1)
            bar.next()
            continue
        discogs_album = discogs_ratings[track_artist].get(track_album, None)
        if discogs_album is None:
            # album not yet in discogs
            results['albums']['miss'].setdefault(track_artist, {})
            results['albums']['miss'][track_artist].setdefault(track_album, 1)
            results['songs']['miss'].setdefault(track_artist, {})
            results['songs']['miss'][track_artist].setdefault(track_name, 0)
            results['songs']['miss'][track_artist][track_name] += 1
            bar.next()
            continue
        discogs_rating = discogs_album['rating'] * convertion_ratio
        if update_songs:
            # update song
            if discogs_rating > track_rating:
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
            if discogs_rating > track_album_rating:
                results['albums']['updated'].setdefault(track_artist, {})
                results['albums']['updated'][track_artist].setdefault(track_album, {'from':track_album_rating, 'to':discogs_rating})
                track.album_rating.set(discogs_rating)
            else:
                # rating not updated
                results['albums']['not_updated'].setdefault(track_artist, {})
                results['albums']['not_updated'][track_artist].setdefault(track_album, {'from':track_album_rating, 'to':discogs_rating})
        ## print "%s - [%i -> %i] %s - [%i -> %i] %s" % (track_artist, track_album_rating, discogs_rating, track_album, track_rating, discogs_rating, track_name)
        bar.next()
    bar.finish()
    ## puts results
    artists_miss = reduce(lambda x,y: x+y, results['artists']['miss'].values() or [0])
    albums_miss = reduce(lambda x,y: x+y, map(lambda x: reduce(lambda x,y: x+y, x.values()), results['albums']['miss'].values()) or [0])
    albums_updated = reduce(lambda x,y: x+y, map(lambda x: len(x.keys()), results['albums']['updated'].values()) or [0])
    albums_not_updated = reduce(lambda x,y: x+y, map(lambda x: len(x.keys()), results['albums']['not_updated'].values()) or [0])
    songs_miss = reduce(lambda x,y: x+y, map(lambda x: reduce(lambda x,y: x+y, x.values()), results['songs']['miss'].values()) or [0])
    songs_updated = reduce(lambda x,y: x+y, map(lambda x: len(x.keys()), results['songs']['updated'].values()) or [0])
    songs_not_updated = reduce(lambda x,y: x+y, map(lambda x: len(x.keys()), results['songs']['not_updated'].values()) or [0])
    print "%i band misses" % artists_miss
    print "%i album misses" % albums_miss
    print "%i albums updated" % albums_updated
    print "%i albums not updated" % albums_not_updated
    print "%i song misses" % songs_miss
    print "%i songs updated" % songs_updated
    print "%i songs not updated" % songs_not_updated


def main(argv):
    apikey = None
    username = None
    datafile = data_file
    update_songs = False
    try:
        opts, args = getopt.getopt(argv, "hu:k:f:s", ["help", "username=", "apikey=", "file=", "songs"])
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-u', '--username'):
            username = arg
        elif opt in ('-k', '--apikey'):
            apikey = arg
        elif opt in ('-f', '--file'):
            datafile = arg
        elif opt in ('-s', '--songs'):
            update_songs = True
    if username is None or apikey is None:
        print str("'username' and apikey are mandatory")
        usage()
        sys.exit(3)
    discogs_ratings = load_data(datafile)
    if discogs_ratings is None:
        discogs_ratings = get_discogs_ratings(username, apikey)
        save_data(datafile, discogs_ratings)
    update_itunes_ratings(discogs_ratings, update_songs)


if __name__ == "__main__":
    main(sys.argv[1:])

