#!/usr/bin/ruby
#
# -*- encoding: utf-8 -*-
# coding: UTF-8
# encoding: utf-8
#
# copyright: 2016-2019, Frederico Martins
# author: Frederico Martins <http://github.com/fscm>
# license: SPDX-License-Identifier: MIT
#
#
# == Synopsis
#
# discogs2itunes: Update iTunes album ratings from Discogs
#
# == Requires
#
# - getoptlong
# - json
# - open-uri
# - progress_bar
# - rb-appscript
# - unidecoder
#
# == Usage
#
# discogs2itunes.rb -u <username> -k <apikey> [-f <filename>] [-h] [-o] [-s]
#
# == Options
#
# -f, --datafile <filename>  datafile name (optional)
# -h, --help                 show help (optional)
# -k, --apikey <api_key>     discogs api key
# -o, --override             override local values (optional)
# -s, --songs                update itunes songs rating instead of album rating (optional)
# -u, --username <username>  discogs username
#


require 'appscript'
require 'getoptlong'
require 'json'
require 'net/http'
require 'progress_bar'
require 'time'
require 'uri'
require 'unidecoder'

I18n.enforce_available_locales = false


$API_BASEURL = "https://api.discogs.com"
$API_FORMAT = 'application/vnd.discogs.v2.plaintext+json'
$API_LIMIT = 100
$CONVERTION_RATIO = 20
$DATA_FILE = 'discogs2itunes.json'
$DATE_NOW = Time.now.utc.to_i


def usage()
  puts ""
  puts "Discogs to iTunes script"
  puts "Usage:"
  puts "  %{discogs2itunes} -u <username> -k <apikey> [-f <filename>] [-h] [-o] [-s]" % {:discogs2itunes => File.basename($0)}
  puts "Options:"
  puts "  -f, --datafile <filename>  datafile name (optional)"
  puts "  -h, --help                 show help (optional)"
  puts "  -k, --apikey <api_key>     discogs api key"
  puts "  -o, --override             override local values (optional)"
  puts "  -s, --songs                update itunes songs rating instead of album rating (optional)"
  puts "  -u, --username <username>  discogs username"
  puts ""
end


def load_data(datafile)
  data = nil
  if File.file?(datafile)
    puts "Loading file..."
    in_file = File.read(datafile)
    begin
      data = JSON.parse(in_file)
    rescue JSON::ParserError
      puts "Invalid data file"
    end
  else
    puts "Data file not found."
  end
  return data
end


def save_data(datafile, data)
  puts "Writing to file..."
  File.open(datafile, 'w') do |out_file|
    out_file.write(JSON.dump(data))
  end
end


def get_discogs_ratings(username, apikey, ratings={})
  puts "Fetching data from Discogs..."
  last_updated = $DATE_NOW
  headers =  {
    'Accept' => $API_FORMAT,
    'Content-Type' => 'application/json',
    'User-Agent' => 'discogs2itunes' }
  query = {
    token: apikey,
    page: '1',
    per_page: $API_LIMIT }
  uri = URI.parse("#{$API_BASEURL}/users/#{username}/collection/folders/0/releases")
  uri.query = URI.encode_www_form(query)
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = true
  get = Net::HTTP::Get.new(uri.request_uri, headers)
  jsondoc = JSON.parse(http.request(get).body)
  total_pages = jsondoc['pagination']['pages'].to_i
  if total_pages < 1
    return {'last_updated' => last_updated, 'ratings' => ratings}
  end
  bar = ProgressBar.new(total_pages, :bar, :counter)
  for page in (1..total_pages)
    query = {
      token: apikey,
      page: page,
      per_page: $API_LIMIT }
    uri.query = URI.encode_www_form(query)
    get = Net::HTTP::Get.new(uri.request_uri, headers)
    jsondoc = JSON.parse(http.request(get).body)
    releases = jsondoc['releases']
    for release in releases
      release_id = release['id'].to_i
      release_instance_id = release['instance_id'].to_i
      release_album_rating = release['rating'].to_i
      release_album = release['basic_information']['title'].to_ascii.downcase
      release_artist = release['basic_information']['artists'].map{ |e| e['name'].gsub(/\(\d+\)$/, '') }.join(' - ').to_ascii.downcase
      #puts "#{release_artist} - [#{release_album_rating}] #{release_album} (#{release_id} / #{release_instance_id})"
      ratings[release_artist] ||= {}
      ratings[release_artist][release_album] ||= {}
      ratings[release_artist][release_album]['rating'] ||= release_album_rating
      ratings[release_artist][release_album]['id'] ||= release_id
      ratings[release_artist][release_album]['instance_id'] ||= release_instance_id
    end
    sleep 0.25
    bar.increment!
  end
  return {'last_updated' => last_updated, 'ratings' => ratings}
end


def update_itunes_ratings(discogs_ratings, update_songs=false, override_values=false)
  puts "Updating iTunes ratings..."

  results = {
    'artists' => {'miss' => {}},
    'albums' => {
      'miss' => {},
      'updated' => {},
      'not_updated' => {} },
    'songs' => {
      'miss' => {},
      'updated' => {},
      'not_updated' => {} } }
  itunes = Appscript.app('iTunes')
  library = itunes.library_playlists['Library']
  tracks = library.tracks.get
  bar = ProgressBar.new(tracks.length, :bar, :counter)
  tracks.each do |track|
    track_artist = track.artist.get.to_ascii.downcase
    track_album = track.album.get.to_ascii.downcase
    track_name = track.name.get.to_ascii.downcase
    track_album_rating = track.album_rating.get.to_i
    track_rating = track.rating.get.to_i
    discogs_artist = discogs_ratings[track_artist]
    if discogs_artist.nil?
      # artist not in discogs
      results['artists']['miss'][track_artist] ||= 1
      bar.increment!
      next
    end
    discogs_album = discogs_ratings[track_artist][track_album]
    if discogs_album.nil?
      # album not yet in discogs
      results['albums']['miss'][track_artist] ||= {}
      results['albums']['miss'][track_artist][track_album] ||= 1
      results['songs']['miss'][track_artist] ||= {}
      results['songs']['miss'][track_artist][track_name] ||= 0
      results['songs']['miss'][track_artist][track_name] += 1
      bar.increment!
      next
    end
    discogs_rating = discogs_album['rating'] * $CONVERTION_RATIO
    if update_songs
      # update song
      if discogs_rating > track_rating || override_values
        # song rating updated
        results['songs']['updated'][track_artist] ||= {}
        results['songs']['updated'][track_artist][track_name] ||= {'from' => track_album_rating, 'to' => discogs_rating}
        track.rating.set(discogs_rating)
      else
        # song rating not updated
        results['songs']['not_updated'][track_artist] ||= {}
        results['songs']['not_updated'][track_artist][track_name] ||= {'from' => track_album_rating, 'to' => discogs_rating}
      end
    else
      # update album
      if discogs_rating > track_album_rating || override_values
        # rating updated
        results['albums']['updated'][track_artist] ||= {}
        results['albums']['updated'][track_artist][track_album] ||= {'from' => track_album_rating, 'to' => discogs_rating}
        track.album_rating.set(discogs_rating)
      else
        # rating not updated
        results['albums']['not_updated'][track_artist] ||= {}
        results['albums']['not_updated'][track_artist][track_album] ||= {'from' => track_album_rating, 'to' => discogs_rating}
      end
    end
    #puts "#{track_artist} - [#{track_album_rating} -> #{discogs_rating}] #{track_album} - [#{track_rating} -> #{discogs_rating}] #{track_name}"
    bar.increment!
  end
  #puts results
  artists_miss = results['artists']['miss'].values.reduce(:+) || 0
  albums_miss = results['albums']['miss'].values.map{ |b| b.values.reduce(:+) }.reduce(:+) || 0
  albums_updated = results['albums']['updated'].values.map { |b| b.values.length }.reduce(:+) || 0
  albums_not_updated = results['albums']['not_updated'].values.map { |b| b.values.length }.reduce(:+) || 0
  songs_miss = results['songs']['miss'].values.map{ |b| b.values.reduce(:+) }.reduce(:+) || 0
  songs_updated = results['songs']['updated'].values.map { |b| b.values.length }.reduce(:+) || 0
  songs_not_updated = results['songs']['not_updated'].values.map { |b| b.values.length }.reduce(:+) || 0
  puts "#{artists_miss} band misses"
  puts "#{albums_miss} album misses" % albums_miss
  puts "#{albums_updated} albums updated" % albums_updated
  puts "#{albums_not_updated} albums not updated" % albums_not_updated
  puts "#{songs_miss} song misses" % songs_miss
  puts "#{songs_updated} songs updated" % songs_updated
  puts "#{songs_not_updated} songs not updated" % songs_not_updated
end


def main()
  apikey = nil
  username = nil
  datafile = $DATA_FILE
  last_updated = 0
  override_values = false
  ratings = {}
  update_songs = false
  if ARGV.length < 1
    usage()
    exit 0
  end
  opts = GetoptLong.new(
  [ '--datafile', '-f', GetoptLong::REQUIRED_ARGUMENT ],
    [ '--help', '-h', GetoptLong::NO_ARGUMENT ],
    [ '--apikey', '-k', GetoptLong::REQUIRED_ARGUMENT ],
    [ '--override', '-o', GetoptLong::NO_ARGUMENT ],
    [ '--songs', '-s', GetoptLong::NO_ARGUMENT ],
    [ '--username', '-u', GetoptLong::REQUIRED_ARGUMENT ]
  )
  begin
    opts.each do |opt, arg|
      case opt
      when "--help"
        usage()
        exit 2
      when "--apikey"
        apikey = arg
      when "--username"
        username = arg
      when "--datafile"
        datafile = arg
      when "--songs"
        update_songs = true
      when "--override"
        override_values = true
      end
    end
  rescue StandardError => my_error_message
    exit 3
  end
  if username.nil? or apikey.nil?
    STDERR.puts "  'username' and 'apikey' are mandatory"
    exit 4
  end
  data = load_data(datafile)
  if data
    last_updated = data.fetch('last_updated', 0).to_i
    ratings = data.fetch('ratings', {})
  end
  data = get_discogs_ratings(username, apikey, ratings)
  save_data(datafile, data)
  update_itunes_ratings(data['ratings'], update_songs, override_values)
end


if __FILE__==$0
  begin
    main
  rescue Interrupt => e
    nil
  end
end
