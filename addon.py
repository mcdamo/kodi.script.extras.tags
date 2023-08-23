# -*- coding: utf-8 -*-
#
# Copyright (C) mcdamo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import xbmc, xbmcgui, xbmcaddon
import json

ADDON = xbmcaddon.Addon()
LANGUAGE = ADDON.getLocalizedString

extras_dir = ADDON.getSetting('extras-folder')
extras_tag = ADDON.getSetting('extras-tag')

def log(message, level=xbmc.LOGDEBUG):
    xbmc.log(msg="[%s] %s" % (ADDON.getAddonInfo('id'), message), level=level)

def jsonrpc(method, params = {}):
    json_query = '{"jsonrpc": "2.0", "method": "%s", "params":%s, "id": 1}' % (method, json.dumps(params))
    json_response = xbmc.executeJSONRPC(json_query)
    response = json.loads(json_response)
    if 'error' in response:
        log(repr(response), xbmc.LOGERROR)
        return None
    return response['result']

def scan(pDialog, media_list, updateCallback):
    total = len(media_list)
    newtag = oldtag = 0
    for idx, media in enumerate(media_list):
        if pDialog.iscanceled():
            return (newtag, oldtag)
        pDialog.update(int(100 * idx/total))
        if extras_tag not in media['tag']:
            media_path = os.path.dirname(media['file'])
            dir = jsonrpc('Files.GetDirectory', {'directory': media_path})
            if dir is None:
                log("Folder Not Found: %s" % (media_path), xbmc.LOGERROR)
                continue
            media_extras = next((file for file in dir['files'] if file['filetype'] == 'directory' and file['label'] == extras_dir), None)
            if media_extras is None:
                continue
            log("%s has Extras" % (media['label']), xbmc.LOGINFO)
            updateCallback(media, media['tag'] + [extras_tag])
            newtag += 1
        else:
            oldtag += 1
    return (newtag, oldtag)

def updateMovie(media, tag):
    jsonrpc('VideoLibrary.SetMovieDetails', {'movieid': media['movieid'], 'tag': tag})

def updateTVShow(media, tag):
    jsonrpc('VideoLibrary.SetTVShowDetails', {'tvshowid': media['tvshowid'], 'tag': tag})

def main():
    # check if Extras tag is in movies DB
    ret = jsonrpc('VideoLibrary.GetTags', {'type': 'movie'})
    movie_tags = ret['tags']
    movie_tag = next((tag for tag in movie_tags if tag['label'] == extras_tag), None)
    ret = jsonrpc("VideoLibrary.GetTags", {'type': 'tvshow'})
    # check if Extras tag is in tvshows DB
    tvshow_tags = ret['tags']
    tvshow_tag = next((tag for tag in tvshow_tags if tag["label"] == extras_tag), None)

    if movie_tag is None and tvshow_tag is None:
        ret = xbmcgui.Dialog().ok(LANGUAGE(32003), LANGUAGE(32004) % extras_tag) # Missing tags
        return
 
    if movie_tag is None:
        ret = xbmcgui.Dialog().yesno(LANGUAGE(32003), LANGUAGE(32005) % (extras_tag, xbmc.getLocalizedString(342))) # Missing from 'Movies'
        if not ret:
            return

    if tvshow_tag is None:
        ret = xbmcgui.Dialog().yesno(LANGUAGE(32003), LANGUAGE(32005) % (extras_tag, xbmc.getLocalizedString(20343))) # Missing from 'TV shows'
        if not ret:
            return

    pDialog = xbmcgui.DialogProgress()
    pDialog.create(LANGUAGE(32006), LANGUAGE(32007))

    movies_newtag = movies_oldtag = tvshows_newtag = tvshows_oldtag = 0

    # scan movies for Extras
    if not pDialog.iscanceled():
        pDialog.update(0, LANGUAGE(32007) % xbmc.getLocalizedString(342))
        ret = jsonrpc('VideoLibrary.GetMovies', {'properties': ['file', 'tag']})
        (movies_newtag, movies_oldtag) = scan(pDialog, ret['movies'], updateMovie)

    # scan tvshows for Extras
    if not pDialog.iscanceled():
        pDialog.update(0, LANGUAGE(32007) % xbmc.getLocalizedString(20343))
        ret = jsonrpc('VideoLibrary.GetTVShows', {'properties': ['file', 'tag']})
        (tvshows_newtag, tvshows_oldtag) = scan(pDialog, ret['tvshows'], updateTVShow)

    pDialog.close()

    ret = xbmcgui.Dialog().ok(LANGUAGE(32000), LANGUAGE(32008) % (movies_newtag, movies_oldtag, tvshows_newtag, tvshows_oldtag))


if __name__ == '__main__':
    main()
