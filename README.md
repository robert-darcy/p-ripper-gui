# p-ripper-gui
A Python-based CD ripper for Linux which automatically names all of the MP3 files created with the song name.

This is my first experiment using Python and is not intended to be a final product.

It should not be duplicated or distributed in any form and may not be used for commercial purposes.

Basically this is a simple program which rips a CD to MP3 files with the click of a single button (and the program only has one button). It generates a MusicBrainz disc id and connects to the MusicBrainz API and retrieves the name of the artist, the album and all the track names. It then rips the disc to MP3 files and renames the tracks with the data retrieved from MusicBrainz and also adds ID3 tags to each track to include the artist, the album, the track name, the track number and the year.

The script has 3 dependencies-

- CD-DISCID

- CDPARANOIA

- LAME

Normally a valid MusicBrainz disc id would be calculated by the LIBDISCID library but due to the configuration of my machine it was not possible to install it, so instead I coded my own function to do this and used the frame offsets of the tracks which are generated by CD-DISCID.

If an internet connection is available the program retrieves data from the MusicBrainz API which will be used later to rename the MP3 files.

If no internet connection is available the program will ask for the name of the album so that it can store MP3s in a folder of that name and skips attempts to rename the MP3 files.

The tracks are ripped to WAV files by CDPARANOIA and this can be a slow process as CDPARANOIA runs intensive error correction routines in order to get the best copy of each track it can. It can also be a bit noisy.

Next MP3 files are created from the WAV files by the LAME encoder. If data was retrieved from the MusicBrainz API it will rename all the tracks and add ID3 tags to each track.

The GUI is made with TKinter.

A few things should be noted-

- I created this for my own personal use, partly to replace my CD ripper shell scripts and partly as a learning exercise. If you want to use this for your own personal use you do so at your own risk. I will accept no liability for damage caused by use of this program.

- This was created to run on Linux. If you are trying to run this on Windows or OSX and it doesn't work for you maybe you can try Docker or a VM.

- As this is a first experiment with Python there aren't any classes so I will not entertain comments regarding this.

- Some more work needs to be done as there are 2 known bugs which I need to get around to fixing.



