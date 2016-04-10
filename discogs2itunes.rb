#!/usr/bin/ruby
#
# -*- encoding: utf-8 -*-
# coding: UTF-8
# encoding: utf-8
#
#
# == Synopsis
#
# discogs2itunes: Update iTunes album ratings from discogs
#
# == Requires
#
# - activesupport
# - getoptlong
# - httparty
# - open-uri
# - progress_bar
# - rb-appscript
#
# == Usage
#
# discogs2itunes.rb -u <username> -k <apikey> [-s -f <filename>]
#
# == Options
#
# --help, -h                  show help
# --apikey, -k <api_key>      discogs api key
# --username, -u <username>   discogs username
# --songs, -s                 update itunes songs rating instead of album rating
# --override, -o              override local values
# --datafile, -f <filename>   datafile name (optional)
#


require 'active_support/inflector' rescue "This script depends on the active_support gem. Please run '(sudo) gem install activesupport'."
require 'appscript'                rescue "This script depends on the rb-appscript gem. Please run '(sudo) gem install rb-appscript'."
require 'getoptlong'
require 'httparty'                 rescue "This script depends on the httparty gem. Please run '(sudo) gem install httparty'."
require 'progress_bar'             rescue "This script depends on the progress_bar gem. Please run '(sudo) gem install progress_bar'."


I18n.enforce_available_locales = false

$api_accept = 'application/vnd.discogs.v2.plaintext+json'
$api_baseurl = 'https://api.discogs.com'
$api_limit = 100
$data_file = 'discogs2itunes.dat'
$convertion_ratio = 20


def usage()
  puts ""
  puts "Discogs to iTunes script"
  puts "Usage:"
  puts "  ruby discogs2itunes.rb -u <username> -k <apikey> [-s -f <filename>]"
  puts "Options:"
  puts "  -h, --help       show help"
  puts "  -k, --apikey     discogs api key"
  puts "  -u, --username   discogs username"
  puts "  -s, --songs      update itunes songs rating instead of album rating"
  puts "  -o, --override   override local values"
  puts "  -f, --datafile   datafile name (optional)"
  puts ""
end


def get_discogs_ratings(username, apikey)
  puts "Geting Discogs ratings..."
  ratings = {}
  headers =  {'Accept' => $api_accept, 'Content-Type' => 'application/json', 'User-Agent' => 'discogs2itunes'}
  query = {token: apikey, page: '1', per_page: $api_limit}
  jsondoc = HTTParty.get("#{$api_baseurl}/users/#{username}/collection/folders/0/releases", :query => query, :headers => headers).parsed_response
  total_pages = jsondoc['pagination']['pages']
  bar = ProgressBar.new(total_pages, :bar, :counter)
  for page in (1..total_pages)
    query = {token: apikey, page: page, per_page: $api_limit}
    jsondoc = HTTParty.get("#{$api_baseurl}/users/#{username}/collection/folders/0/releases", :query => query, :headers => headers).parsed_response
    releases = jsondoc['releases']
    for release in releases
      release_id = release['id'].to_i
      release_instance_id = release['instance_id'].to_i
      release_album_rating = release['rating'].to_i
      release_album = release['basic_information']['title'].downcase.strip.parameterize
      release_artist = release['basic_information']['artists'].map{ |e| e['name'].gsub(/\(\d+\)$/, '') }.join(' - ').downcase.strip.parameterize
      ## puts "#{release_artist} - [#{release_album_rating}] #{release_album} (#{release_id} / #{release_instance_id})"
      ratings[release_artist] ||= {}
      ratings[release_artist][release_album] ||= {}
      ratings[release_artist][release_album]['rating'] ||= release_album_rating
      ratings[release_artist][release_album]['id'] ||= release_id
      ratings[release_artist][release_album]['instance_id'] ||= release_instance_id
    end
    sleep 0.25
    bar.increment!
  end
  return ratings
end


def load_data(datafile)
  data = nil
  if File.file?(datafile)
    puts "Loading file..."
    in_file = File.binread(datafile)
    data = Marshal.load(in_file)
  else
    puts "Data file not found."
  end
  return data
end


def save_data(datafile, data)
  puts "Writing to file..."
  File.open(datafile, 'wb') do |out_file|
    out_file.write(Marshal.dump(data))
  end
end


def update_itunes_ratings(discogs_ratings, update_songs=false, override_values=false)
  puts "Updating iTunes ratings..."
  results = {'artists' => {'miss' => {}}, 'albums' => {'miss' => {}, 'updated' => {}, 'not_updated' => {}}, 'songs' => {'miss' => {}, 'updated' => {}, 'not_updated' => {}}}
  itunes = Appscript.app('iTunes')
  tracks = itunes.tracks.get
  total_tracks = tracks.length
  bar = ProgressBar.new(total_tracks, :bar, :counter)
  tracks.each do |track|
    track_artist = track.artist.get.downcase.strip.parameterize
    track_album = track.album.get.downcase.strip.parameterize
    track_name = track.name.get.downcase.strip.parameterize
    track_album_rating = track.album_rating.get
    track_rating = track.rating.get.to_i
    ## puts "#{track_artist} - [#{track_album_rating}] #{track_album} - [#{track_rating}] #{track_name}"
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
    discogs_rating = discogs_album['rating'] * $convertion_ratio
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
    ## puts "#{track_artist} - [#{track_album_rating} -> #{discogs_rating}] #{track_album} - [#{track_rating} -> #{discogs_rating}] #{track_name}"
    bar.increment!
  end
  ## puts results
  artists_miss = results['artists']['miss'].values.reduce(:+) || 0
  albums_miss = results['albums']['miss'].values.map{ |b| b.values.reduce(:+) }.reduce(:+) || 0
  albums_updated = results['albums']['updated'].values.map { |b| b.values.length }.reduce(:+) || 0
  albums_not_updated = results['albums']['not_updated'].values.map { |b| b.values.length }.reduce(:+) || 0
  songs_miss = results['songs']['miss'].values.map{ |b| b.values.reduce(:+) }.reduce(:+) || 0
  songs_updated = results['songs']['updated'].values.map { |b| b.values.length }.reduce(:+) || 0
  songs_not_updated = results['songs']['not_updated'].values.map { |b| b.values.length }.reduce(:+) || 0
  puts "%i band misses" % artists_miss
  puts "%i album misses" % albums_miss
  puts "%i albums updated" % albums_updated
  puts "%i albums not updated" % albums_not_updated
  puts "%i song misses" % songs_miss
  puts "%i songs updated" % songs_updated
  puts "%i songs not updated" % songs_not_updated
end


def main()
  apikey = nil
  username = nil
  datafile = $data_file
  update_songs = false
  override_values = false
  opts = GetoptLong.new(
    [ '--help', '-h', GetoptLong::NO_ARGUMENT ],
    [ '--apikey', '-k', GetoptLong::REQUIRED_ARGUMENT ],
    [ '--username', '-u', GetoptLong::REQUIRED_ARGUMENT ],
    [ '--songs', '-s', GetoptLong::NO_ARGUMENT ],
    [ '--override', '-o', GetoptLong::NO_ARGUMENT ],
    [ '--datafile', '-f', GetoptLong::REQUIRED_ARGUMENT ]
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
  rescue StandardError=>my_error_message
    usage()
    exit 3
  end
  if username.nil? or apikey.nil?
    usage()
    exit 4
  end
  discogs_ratings = load_data(datafile)
  if discogs_ratings.nil?
    discogs_ratings = get_discogs_ratings(username, apikey)
    save_data(datafile, discogs_ratings)
  end
  update_itunes_ratings(discogs_ratings, update_songs, override_values)
end


if __FILE__==$0
  begin
    main
  rescue Interrupt => e
    nil
  end
end

