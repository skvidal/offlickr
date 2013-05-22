offlickr
========

<p>Command line backup tool for Flickr</p>


<p>It allows you to download photos, videos, metadata 
(title, tags, description, geotags, notes, comments), and photosets.</p>


<pre>
Options:
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
