#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
# Offlickr
# Hugo Haas -- mailto:hugo@larve.net -- http://larve.net/people/hugo/
# Homepage: http://larve.net/people/hugo/2005/12/offlickr/
# License: GPLv2
#
# Daniel Drucker <dmd@3e.org> contributed:
#   * wget patch
#   * backup of videos as well
#   * updated to Beej's Flickr API version 1.2 (required)

# added by seth Vidal - skvidal@fedoraproject.org - 2013-05-22
#   * optparse it
#   * dateutil parsing for time
#   * fetch flickrid by fapi - not ask for it
#   * applied patches from upstream


import sys
import libxml2
import urllib
from optparse import OptionParser
import time
import dateutil
import dateutil.parser
import os
import threading




# Beej's Python Flickr API
# http://beej.us/flickr/flickrapi/


from flickrapi import FlickrAPI
import logging

__version__ = '0.22 - 2009-03-20'
maxTime = '9999999999'

# Gotten from Flickr

flickrAPIKey = '1391fcd0a9780b247cd6a101272acf71'
flickrSecret = 'fd221d0336de3b6d'


class Offlickr:

    def __init__(
        self,
        key,
        secret,
        httplib=None,
        dryrun=False,
        verbose=False,
        ):
        """Instantiates an Offlickr object
        An API key is needed, as well as an API secret"""

        self.__flickrAPIKey = key
        self.__flickrSecret = secret
        self.__httplib = httplib

        # Get authentication token
        # note we must explicitly select the xmlnode parser to be compatible with FlickrAPI 1.2

        self.fapi = FlickrAPI(self.__flickrAPIKey, self.__flickrSecret,
                              format='xmlnode')
        (token, frob) = self.fapi.get_token_part_one()
        if not token:
            raw_input('Press ENTER after you authorized this program')
        self.fapi.get_token_part_two((token, frob))
        self.token = token
        test_login = self.fapi.test_login()
        uid = test_login.user[0]['id']
        self.flickrUserId = uid
        self.dryrun = dryrun
        self.verbose = verbose

    def __testFailure(self, rsp):
        """Returns whether the previous call was successful"""

        if rsp['stat'] == 'fail':
            print 'Error!'
            return True
        else:
            return False

    def getPhotoList(self, dateLo, dateHi):
        """Returns a list of photo given a time frame"""

        n = 0
        flickr_max = 500
        photos = []

        print 'Retrieving list of photos'
        while True:
            if self.verbose:
                print 'Requesting a page...'
            n = n + 1
            rsp = self.fapi.photos_search(
                api_key=self.__flickrAPIKey,
                auth_token=self.token,
                user_id=self.flickrUserId,
                per_page=str(flickr_max),
                page=str(n),
                min_upload_date=dateLo,
                max_upload_date=dateHi,
                )
            if self.__testFailure(rsp):
                return None
            if rsp.photos[0]['total'] == '0':
                return None
            photos += rsp.photos[0].photo
            if self.verbose:
                print ' %d photos so far' % len(photos)
            if len(photos) >= int(rsp.photos[0]['total']):
                break

        return photos

    def getGeotaggedPhotoList(self, dateLo, dateHi):
        """Returns a list of photo given a time frame"""

        n = 0
        flickr_max = 500
        photos = []

        print 'Retrieving list of photos'
        while True:
            if self.verbose:
                print 'Requesting a page...'
            n = n + 1
            rsp = \
                self.fapi.photos_getWithGeoData(api_key=self.__flickrAPIKey,
                    auth_token=self.token, user_id=self.flickrUserId,
                    per_page=str(flickr_max), page=str(n))
            if self.__testFailure(rsp):
                return None
            if rsp.photos[0]['total'] == '0':
                return None
            photos += rsp.photos[0].photo
            if self.verbose:
                print ' %d photos so far' % len(photos)
            if len(photos) >= int(rsp.photos[0]['total']):
                break

        return photos

    def getPhotoLocation(self, pid):
        """Returns a string containing location of a photo (in XML)"""

        rsp = \
            self.fapi.photos_geo_getLocation(api_key=self.__flickrAPIKey,
                auth_token=self.token, photo_id=pid)
        if self.__testFailure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        info = doc.xpathEval('/rsp/photo')[0].serialize()
        doc.freeDoc()
        return info

    def getPhotoLocationPermission(self, pid):
        """Returns a string containing location permision for a photo (in XML)"""

        rsp = \
            self.fapi.photos_geo_getPerms(api_key=self.__flickrAPIKey,
                auth_token=self.token, photo_id=pid)
        if self.__testFailure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        info = doc.xpathEval('/rsp/perms')[0].serialize()
        doc.freeDoc()
        return info

    def getPhotosetList(self):
        """Returns a list of photosets for a user"""

        rsp = self.fapi.photosets_getList(api_key=self.__flickrAPIKey,
                auth_token=self.token, user_id=self.flickrUserId)
        if self.__testFailure(rsp):
            return None
        return rsp.photosets[0].photoset

    def getPhotosetInfo(self, pid, method):
        """Returns a string containing information about a photoset (in XML)"""

        rsp = method(api_key=self.__flickrAPIKey,
                     auth_token=self.token, photoset_id=pid)
        if self.__testFailure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        info = doc.xpathEval('/rsp/photoset')[0].serialize()
        doc.freeDoc()
        return info

    def getPhotoMetadata(self, pid):
        """Returns an array containing containing the photo metadata (as a string), and the format of the photo"""

        if self.verbose:
            print 'Requesting metadata for photo %s' % pid
        rsp = self.fapi.photos_getInfo(api_key=self.__flickrAPIKey,
                auth_token=self.token, photo_id=pid)
        if self.__testFailure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        metadata = doc.xpathEval('/rsp/photo')[0].serialize()
        doc.freeDoc()
        return [metadata, rsp.photo[0]['originalformat']]

    def getPhotoComments(self, pid):
        """Returns an XML string containing the photo comments"""

        if self.verbose:
            print 'Requesting comments for photo %s' % pid
        rsp = \
            self.fapi.photos_comments_getList(api_key=self.__flickrAPIKey,
                auth_token=self.token, photo_id=pid)
        if self.__testFailure(rsp):
            return None
        doc = libxml2.parseDoc(rsp.xml)
        comments = doc.xpathEval('/rsp/comments')[0].serialize()
        doc.freeDoc()
        return comments

    def getPhotoSizes(self, pid):
        """Returns a string with is a list of available sizes for a photo"""

        rsp = self.fapi.photos_getSizes(api_key=self.__flickrAPIKey,
                auth_token=self.token, photo_id=pid)
        if self.__testFailure(rsp):
            return None
        return rsp

    def getOriginalPhoto(self, pid):
        """Returns a URL which is the original photo, if it exists"""

        source = None
        rsp = self.getPhotoSizes(pid)
        if rsp == None:
            return None
        for s in rsp.sizes[0].size:
            if s['label'] == 'Original':
                source = s['source']
        for s in rsp.sizes[0].size:
            if s['label'] == 'Video Original':
                source = s['source']
        return [source, s['label'] == 'Video Original']

    def __downloadReportHook(
        self,
        count,
        blockSize,
        totalSize,
        ):

        if not self.__verbose:
            return
        p = ((100 * count) * blockSize) / totalSize
        if p > 100:
            p = 100
        print '\r %3d %%' % p,
        sys.stdout.flush()

    def downloadURL(
        self,
        url,
        target,
        filename,
        verbose=False,
        ):
        """Saves a photo in a file"""

        if self.dryrun:
            return
        self.__verbose = verbose
        tmpfile = '%s/%s.TMP' % (target, filename)
        if self.__httplib == 'wget':
            cmd = 'wget -q -t 0 -T 120 -w 10 -c -O %s %s' % (tmpfile,
                    url)
            os.system(cmd)
        else:
            urllib.urlretrieve(url, tmpfile,
                               reporthook=self.__downloadReportHook)
        os.rename(tmpfile, '%s/%s' % (target, filename))

def fileWrite(
    dryrun,
    directory,
    filename,
    string,
    ):
    """Write a string into a file"""

    if dryrun:
        return
    if not os.access(directory, os.F_OK):
        os.makedirs(directory)
    f = open(directory + '/' + filename, 'w')
    f.write(string)
    f.close()
    print 'Written as', filename


class photoBackupThread(threading.Thread):

    def __init__(
        self,
        sem,
        i,
        total,
        id,
        title,
        offlickr,
        target,
        hash_level,
        getPhotos,
        doNotRedownload,
        overwritePhotos,
        ):

        self.sem = sem
        self.i = i
        self.total = total
        self.id = id
        self.title = title
        self.offlickr = offlickr
        self.target = target
        self.hash_level = hash_level
        self.getPhotos = getPhotos
        self.doNotRedownload = doNotRedownload
        self.overwritePhotos = overwritePhotos
        threading.Thread.__init__(self)

    def run(self):
        backupPhoto(
            self.i,
            self.total,
            self.id,
            self.title,
            self.target,
            self.hash_level,
            self.offlickr,
            self.doNotRedownload,
            self.getPhotos,
            self.overwritePhotos,
            )
        self.sem.release()


def backupPhoto(
    i,
    total,
    id,
    title,
    target,
    hash_level,
    offlickr,
    doNotRedownload,
    getPhotos,
    overwritePhotos,
    ):

    print str(i) + '/' + str(total) + ': ' + id + ': '\
         + title.encode('utf-8')
    td = target_dir(target, hash_level, id)
    if doNotRedownload and os.path.isfile(td + '/' + id + '.xml')\
         and os.path.isfile(td + '/' + id + '-comments.xml')\
         and (not getPhotos or getPhotos and os.path.isfile(td + '/'
               + id + '.jpg')):
        print 'Photo %s already downloaded; continuing' % id
        return

    # Get Metadata

    metadataResults = offlickr.getPhotoMetadata(id)
    if metadataResults == None:
        print 'Failed!'
        sys.exit(2)
    metadata = metadataResults[0]
    format = metadataResults[1]
    t_dir = target_dir(target, hash_level, id)

    # Write metadata

    fileWrite(offlickr.dryrun, t_dir, id + '.xml', metadata)

    # Get comments

    photoComments = offlickr.getPhotoComments(id)
    fileWrite(offlickr.dryrun, t_dir, id + '-comments.xml',
              photoComments)

    # Do we want the picture too?

    if not getPhotos:
        return
    [source, isVideo] = offlickr.getOriginalPhoto(id)

    if source == None:
        print 'Oopsie, no photo found'
        return

    # if it's a Video, we cannot trust the format that getInfo told us.
    # we have to make an extra round trip to grab the Content-Disposition
    isPrivateFailure = False

    if isVideo:
        sourceconnection = urllib.urlopen(source)
        try:
            format = sourceconnection.headers['Content-Disposition'].split('.')[-1].rstrip('"')
        except:
            print 'warning: private videos cannot be backed up due to a Flickr bug'
            format = 'privateVideofailure'
            isPrivateFailure = True

    filename = id + '.' + format


    if os.path.isfile('%s/%s' % (t_dir, filename))\
         and not overwritePhotos:
        print '%s already downloaded... continuing' % filename
        return
    if not isPrivateFailure:
        print 'Retrieving ' + source + ' as ' + filename
        offlickr.downloadURL(source, t_dir, filename, verbose=True)
        print 'Done downloading %s' % filename


def backupPhotos(
    threads,
    offlickr,
    target,
    hash_level,
    dateLo,
    dateHi,
    getPhotos,
    doNotRedownload,
    overwritePhotos,
    ):
    """Back photos up for a particular time range"""

    if dateHi == maxTime:
        t = time.time()
        print 'For incremental backups, the current time is %.0f' % t
        print "You can rerun the program with '-f %.0f'" % t

    photos = offlickr.getPhotoList(dateLo, dateHi)
    if photos == None:
        print 'No photos found'
        sys.exit(1)

    total = len(photos)
    print 'Backing up', total, 'photos'

    if threads > 1:
        concurrentThreads = threading.Semaphore(threads)
    i = 0
    for p in photos:
        i = i + 1
        pid = str(int(p['id']))  # Making sure we don't have weird things here
        if threads > 1:
            concurrentThreads.acquire()
            downloader = photoBackupThread(
                concurrentThreads,
                i,
                total,
                pid,
                p['title'],
                offlickr,
                target,
                hash_level,
                getPhotos,
                doNotRedownload,
                overwritePhotos,
                )
            downloader.start()
        else:
            backupPhoto(
                i,
                total,
                pid,
                p['title'],
                target,
                hash_level,
                offlickr,
                doNotRedownload,
                getPhotos,
                overwritePhotos,
                )


def backupLocation(
    threads,
    offlickr,
    target,
    hash_level,
    dateLo,
    dateHi,
    doNotRedownload,
    ):
    """Back photo locations up for a particular time range"""

    if dateHi == maxTime:
        t = time.time()
        print 'For incremental backups, the current time is %.0f' % t
        print "You can rerun the program with '-f %.0f'" % t

    photos = offlickr.getGeotaggedPhotoList(dateLo, dateHi)
    if photos == None:
        print 'No photos found'
        sys.exit(1)

    total = len(photos)
    print 'Backing up', total, 'photo locations'

    i = 0
    for p in photos:
        i = i + 1
        pid = str(int(p['id']))  # Making sure we don't have weird things here
        td = target_dir(target, hash_level, pid) + '/'
        if doNotRedownload and os.path.isfile(td + pid + '-location.xml'
                ) and os.path.isfile(td + pid
                 + '-location-permissions.xml'):
            print pid + ': Already there'
            continue
        location = offlickr.getPhotoLocation(pid)
        if location == None:
            print 'Failed!'
        else:
            fileWrite(offlickr.dryrun, target_dir(target, hash_level,
                      pid), pid + '-location.xml', location)
        locationPermission = offlickr.getPhotoLocationPermission(pid)
        if locationPermission == None:
            print 'Failed!'
        else:
            fileWrite(offlickr.dryrun, target_dir(target, hash_level,
                      pid), pid + '-location-permissions.xml',
                      locationPermission)


def backupPhotosets(offlickr, target, hash_level):
    """Back photosets up"""

    photosets = offlickr.getPhotosetList()
    if photosets == None:
        print 'No photosets found'
        sys.exit(0)

    total = len(photosets)
    print 'Backing up', total, 'photosets'

    i = 0
    for p in photosets:
        i = i + 1
        pid = str(int(p['id']))  # Making sure we don't have weird things here
        print str(i) + '/' + str(total) + ': ' + pid + ': '\
             + p.title[0].text.encode('utf-8')

        # Get Metadata

        info = offlickr.getPhotosetInfo(pid,
                offlickr.fapi.photosets_getInfo)
        if info == None:
            print 'Failed!'
        else:
            fileWrite(offlickr.dryrun, target_dir(target, hash_level,
                      pid), 'set_' + pid + '_info.xml', info)
        photos = offlickr.getPhotosetInfo(pid,
                offlickr.fapi.photosets_getPhotos)
        if photos == None:
            print 'Failed!'
        else:
            fileWrite(offlickr.dryrun, target_dir(target, hash_level,
                      pid), 'set_' + pid + '_photos.xml', photos)


        # Do we want the picture too?


def target_dir(target, hash_level, id):
    dir = target
    i = 1
    while i <= hash_level:
        dir = dir + '/' + id[len(id) - i]
        i = i + 1
    return dir


def main(args):
    """Command-line interface"""


    # Parse command line    
    
    parser = OptionParser(version = "1.0")
    parser.add_option('-c', dest='threads', default=1, 
        help="number of threads to run to backup photos")
    parser.add_option('-f', dest='start', default='0', 
        help="start of date to range, most date strings accepted or seconds from the epoch")    
    parser.add_option('-t', dest='end', default=maxTime,
        help="end of date to range, most date strings accepted or seconds from the epoch")
    parser.add_option('-d', dest='dest', default='dst', 
        help="directory for saving files")
    parser.add_option('-l', dest='hash_level', default=0, 
        help="levels of directory hashes")
    parser.add_option('-p', dest='get_photos', default=False, action='store_true',
        help="back up photos in addition to photo metadata")
    parser.add_option('-n', dest='do_not_redownload', default=False, action='store_true',
        help="do not redownload anything which has already been downloaded")
    parser.add_option('-o', dest='overwrite_photos', default=False, action='store_true',
        help="overwrite photo, even if it already exists")
    parser.add_option('-L', dest='photo_locations', default=False, action='store_true',
        help="back up human-readable photo locations and permissions to separate files")
    parser.add_option('-s', dest='photosets', default=False, action='store_true',
        help="back up all photosets (time range is ignored")
    parser.add_option('-w', dest='use_wget', default=False, action='store_true',
        help="use wget instead of internal Python HTTP library - preserves picture timestamps")
    parser.add_option('-v', dest='verbose', default=False, action='store_true',
        help="verbose output")
    parser.add_option('-N', dest='dry_run', default=False, action='store_true',
        help='dry run')

    opts,args = parser.parse_args(args)

    if not os.path.isdir(opts.dest):
        print opts.dest + ' is not a directory; please fix that.'
        sys.exit(1)
    
    # make hash_level an int
    opts.hash_level = int(opts.hash_level)
    
    # thread count is an int 
    opts.threads = int(opts.threads)
    
    if opts.use_wget:
        httplib = 'wget'
    else:
        httplib = None

    # parse out the time strings to seconds from the epoch
    try:
        start = time.mktime(dateutil.parser.parse(opts.start).timetuple())
    except (ValueError, OverflowError), e:
        start = float(opts.start)
    except:
        print 'Could not parse time string of %s - try something simpler' % opts.start
        sys.exit(1)
        
    try:
        end = time.mktime(dateutil.parser.parse(opts.end).timetuple())
    except (ValueError, OverflowError), e:
        end = float(opts.end)
    except:
        print 'Could not parse time string of %s - try something simpler' % opts.end
        sys.exit(1)



    offlickr = Offlickr(
        flickrAPIKey,
        flickrSecret,
        httplib,
        opts.dry_run,
        opts.verbose,
        )

    if opts.photosets:
        backupPhotosets(offlickr, opts.dest, opts.hash_level)
    
    elif opts.photo_locations:
        backupLocation(
            opts.threads,
            offlickr,
            opts.dest,
            opts.hash_level,
            start,
            end,
            opts.do_not_redownload,
            )
    else:
        backupPhotos(
            opts.threads,
            offlickr,
            opts.dest,
            opts.hash_level,
            start,
            end,
            opts.get_photos,
            opts.do_not_redownload,
            opts.overwrite_photos,
            )


if __name__ == '__main__':
    main(sys.argv[1:])
