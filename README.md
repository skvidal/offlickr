offlickr
========
<p>Command line backup tool for Flickr</p>

Forked from: https://code.google.com/p/offlickr/

<p>It allows you to download photos, videos, metadata 
(title, tags, description, geotags, notes, comments), and photosets.</p>

Options:
--------

<pre>

  --version      show program's version number and exit
  -h, --help     show this help message and exit
  -c THREADS     number of threads to run to backup photos
  -f START       start of date to range, most date strings accepted or seconds
                 from the epoch
  -t END         end of date to range, most date strings accepted or seconds
                 from the epoch
  -d DEST        directory for saving files
  -l HASH_LEVEL  levels of directory hashes
  -p             back up photos in addition to photo metadata
  -n             do not redownload anything which has already been downloaded
  -o             overwrite photo, even if it already exists
  -L             back up human-readable photo locations and permissions to
                 separate files
  -s             back up all photosets (time range is ignored
  -w             use wget instead of internal Python HTTP library - preserves
                 picture timestamps
  -v             verbose output
  -N             dry run
</pre>


Example usage:
--------------

`offlickr.py -f 2013-01-01 -t 2013-02-01 -p -n -w -c 5 -d /some/path`

This does the following:
* download all the photos and metadata from your account  (-p)
* between: 2013-01-01 and 2013-02-01 (-f and -t)
* use 5 threads to download (-c).
* use 'wget' to download the files. (-w)
* not redownload anything that already exists. (-n)
* download all the files to /some/path (-d)



Originally written by: 
----------------------

* Hugo Haas -- mailto:hugo@larve.net -- http://larve.net/people/hugo/
     Homepage: http://larve.net/people/hugo/2005/12/offlickr/

Augmented by:

* Daniel Drucker <dmd@3e.org>
* Seth Vidal <skvidal@fedoraproject.org>


