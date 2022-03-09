"""This simple CD ripper is my first attempt at creating a
functional program for Linux.

It has 3 dependencies:

- cd-discid
- cdparanoia
- lame

It does not have any menus or settings, just 1 big button.

If no internet connection is available it gives the option to do
a straight rip to MP3 in a folder named by the user, otherwise
it gets all the album details from the musicbrainz API and
uses those to create named MP3s in a folder whose name is
a combination of the name of the artist and the album.

Instead of using the libdiscid module, the disc id is calculated
by the calculate_disc_id function which I coded and
which uses frame offsets supplied by cd-discid.

cdparanoia rips the CD to WAV files - the speed of this
depends on the CD and just how paranoid about it
cdparanoia feels.

lame creates new MP3 files from the WAV files and includes
ID3 tags with artist, album, year and track information.

* This program does NOT account for disc id collisions *
"""

import os
import os.path
import subprocess
import socket
from urllib.request import Request, urlopen
import hashlib
import codecs
import json
import tkinter as tk
import tkinter.messagebox as popup
from tkinter import Frame
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring

from image_for_button import image_for_button



main_window = tk.Tk()
main_window.title('Python Ripper v0.6')

window_left = int((main_window.winfo_screenwidth() - 210) / 2)
window_top = int((main_window.winfo_screenheight() - 90) / 2)

main_window.geometry(f"210x90+{window_left}+{window_top}")
main_window.resizable(0, 0)
main_window.config(bg='#d9d9d9')

button_image = tk.PhotoImage(data=image_for_button)



current_directory = os.getcwd()



def display_popup(popup_type, this_title='hello', this_message='dog fucker'):

    answer = None

    if popup_type == 'error':
        popup.showwarning(title=this_title, message=this_message)
    elif popup_type == 'success':
        popup.showinfo(title=this_title, message=this_message)
    else:
        answer = popup.askyesno(title=this_title, message=this_message)

    return answer



def clean_up():
    # sometimes a track00.cdda.wav gets left behind
    if os.path.isfile('track00.cdda.wav'):
        try:
            os.remove('track00.cdda.wav')
        except:
            display_popup('error',
                          'Error',
                          'There was an error tidying up after ripping \
                           the CD')
    return None



def convert_wav_to_mp3(artist,
                       album_name,
                       year,
                       track_number,
                       number_of_tracks,
                       track_name):

    wav_filename = 'track%02d.cdda.wav' % track_number
    mp3_name = '%02d - %s.mp3' % (track_number, track_name)
    track_x_of_xx = '%d/%d' % (track_number, number_of_tracks)
    command_string = 'lame -mj -V0 --tt "%s" --tn "%s" --ta "%s" --tl "%s" \
                      --ty "%s" --id3v2-only %s "%s"' % (track_name,
                                                         track_x_of_xx,
                                                         artist,
                                                         album_name,
                                                         year,
                                                         wav_filename,
                                                         mp3_name)
    wav_to_mp3 = subprocess.Popen(command_string,
                                  shell=True,
                                  close_fds=True
                                  )
    wav_to_mp3.wait()
    os.remove(wav_filename)

    return None



def rip_cd_to_wav():

    cd_to_wav = subprocess.Popen('cdparanoia -B',
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 close_fds=True
                                 )
    cd_to_wav.wait()

    return None



def rip_disc_with_names(album_info):

    folder_name = album_info[0] + ' - ' + album_info[1]
    folder_path = os.path.join(current_directory, folder_name)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_name)
    os.chdir(folder_name)

    if album_info[4] > 1:
        subfolder_name = 'disc %d of %d' % (album_info[3] + 1, album_info[4])
        subfolder_path = os.path.join(folder_path, subfolder_name)
        if not os.path.isdir(subfolder_path):
            os.makedirs(subfolder_name)
        os.chdir(subfolder_name)

    rip_cd_to_wav()

    track_number = 0
    for track in album_info[5]:
        track_number += 1
        convert_wav_to_mp3(album_info[0],
                             album_info[1],
                             album_info[2],
                             track_number,
                             len(album_info[5]),
                             track)

    message = "{} successfully ripped to highest quality, joint stereo, \
               variable bit length encoded MP3".format(folder_name)
    display_popup('success', 'Success', message)

    return None



def parse_disc_info(disc_data):

    disc_dict = dict(disc_data)

    # cycle through the list discs (media) to find the correct disc by matching the disc-id
    discs_in_box = len(disc_dict['releases'][0]['media'])
    for disc_number in range(0, discs_in_box):
        disc_versions_released = disc_dict['releases'][0]['media'][disc_number]['discs']
        for disc_version in range(0, len(disc_versions_released)):
            if (disc_versions_released[disc_version]['id'] == disc_dict['id']):
                this_disc_number = disc_number
                break
    artist           = disc_dict['releases'][0]['artist-credit'][0]['name']
    album_name       = disc_dict['releases'][0]['title']
    
    if 'date' in disc_dict['releases'][0]:
        year             = disc_dict['releases'][0]['date'][:4]
    else:
        year = ''
    
    number_of_tracks = int(disc_dict['releases'][0]['media'][this_disc_number]['track-count'])

    track_list = []

    for track in range(0, number_of_tracks):
        track_list.append(disc_dict['releases'][0]['media'][this_disc_number]['tracks'][track]['title'])

    album_info = [artist, album_name, year, this_disc_number, discs_in_box,
                  track_list]

    return album_info  



def get_disc_info(disc_id):

    url = 'https://musicbrainz.org/ws/2/discid/' + disc_id + \
          '?inc=artists+recordings&fmt=json'
    headers = {'User-Agent': 'Python Ripper/0.3 \
               (http://www.your-website-here.com)'}
    request = Request(url, headers=headers)

    with urlopen(request) as page:
        # should try except here to catch when cock-up occurs
        disc_info_bytes = page.read()
        disc_info = json.loads(disc_info_bytes.decode('UTF-8'))

    return disc_info



def calculate_disc_id(toc):

    shash = hashlib.sha1()

    toc_length = len(toc)

    first_track_number = 1
    last_track_number  = toc_length - 1
    lead_out_offset    = toc[toc_length - 1]

    first_track_hex     = b'%02X' % first_track_number
    last_track_hex      = b'%02X' % last_track_number
    lead_out_offset_hex = b'%08X' % int(lead_out_offset)

    disc_id = shash.update(first_track_hex)
    disc_id = shash.update(last_track_hex)
    disc_id = shash.update(lead_out_offset_hex)

    for i in range(0,99):
        if i < last_track_number:
            this_offset = int(toc[i])
        else:
            this_offset = 0
        this_offset_hex = b'%08X' % this_offset
        disc_id = shash.update(this_offset_hex)

    disc_id_b64 = codecs.encode(codecs.decode(shash.hexdigest(), 'hex'), 'base64').decode()

    fixed_string_1 = disc_id_b64.replace('+', '.')
    fixed_string_2 = fixed_string_1.replace('/', '_')
    fixed_string_3 = fixed_string_2.replace('=', '-')
    disc_id_b64    = fixed_string_3[:-1]

    return disc_id_b64



def run_cddisc_id():

    discid_data = subprocess.Popen('cd-discid --musicbrainz',
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT
                                   )
    return discid_data



def rip_disc_advanced():

    discid_data = run_cddisc_id()

    for line in discid_data.stdout.readlines():

        shell_output = str(line)

        if 'No medium found' in shell_output:
            display_popup('error', 'Error', 'No CD in drive')
        else:
            shell_output_no_newline = shell_output[:-3]
            disc_frames             = shell_output_no_newline.split(' ')
            number_of_tracks        = disc_frames.pop(0)
            disc_id                 = calculate_disc_id(disc_frames)
            disc_data               = get_disc_info(disc_id)
            album_info              = parse_disc_info(disc_data)
            rip_disc_with_names(album_info)
            clean_up()
            os.chdir(current_directory)

    return None



def make_new_directory(folder_name=None):
    if not folder_name:
        folder_name = askstring('Album Name', 'Enter the name of the album')
        try:
            os.makedirs(folder_name)
        except:
            display_popup('error', 'Error', 'That folder already exists')
            make_new_directory()
        else:
            os.chdir(folder_name)
    return folder_name



def rip_disc_basic():

    folder_name = make_new_directory()

    rip_cd_to_wav()
    clean_up()
    number_of_wavs = len(os.listdir())
    
    for track_number in range(1, number_of_wavs + 1):
        wav_filename = 'track%02d.cdda.wav' % track_number
        mp3_name = '%02d - untitled.mp3' % track_number
        command_string = 'lame -mj -V0 %s "%s"' % (wav_filename, mp3_name)
        wav_to_mp3 = subprocess.Popen(command_string,
                                  shell=True,
                                  close_fds=True
                                  )
        wav_to_mp3.wait()
        os.remove(wav_filename)

    message = "{} successfully ripped to highest quality, joint stereo, \
               variable bit length encoded MP3".format(folder_name)
    display_popup('success', 'Success', message)



def check_internet_connection(host='8.8.8.8', port=53, timeout=3):

    answer = None

    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return (True, answer)
    except socket.error:
        answer = display_popup('warning',
                               'Warning',
                               'Internet connection not available.\nDo \
                                you wish to proceed anyway?')
        return (False, answer)



def main():

    internet, answer = check_internet_connection()

    if not internet:
        if answer:
            rip_disc_basic()
        else:
            main_window.destroy()
    else:
        rip_disc_advanced()

    return None



def show_start_message():
    global window_left, window_top



def close_message():
    message_window.destroy()



ripper_button = tk.Button(main_window, image=button_image, command=main)

ripper_button.pack(padx=10,pady=10)

message_window = tk.Toplevel(main_window)
message_window.title("About Python Ripper")
message_window.geometry(f"420x320+{window_left+30}+{int((main_window.winfo_screenheight() - 320) / 2)}")
message_window.wm_attributes("-topmost", 1)

message_text = "This simple CD ripper is \
my first attempt at creating a \
functional program for Linux.\n\
\n\
It has 3 dependencies:\n\
\n\
∙ cd-discid\n\
∙ cdparanoia\n\
∙ lame\n\
\n\
It does not have any menus or settings, just 1 big button.\n\
\n\
If no internet connection is available it gives the option to do \
a straight rip to MP3 in a folder named by the user - otherwise \
it gets all the album details from the musicbrainz API and \
uses those to create named MP3s in a folder whose name is \
a combination of the name of the artist and the album.\n\
\n\
Instead of using the libdiscid module, the disc id is calculated \
by the calculate_disc_id function which I coded and \
which uses frame offsets supplied by cd-discid.\n\
\n\
cdparanoia rips the CD to WAV files - the speed of this \
depends on the CD and just how paranoid about it \
cdparanoia feels.\n\
\n\
lame creates new MP3 files from the WAV files and includes \
ID3 tags with artist, album, year and track information.\n\
\n\
* This program does NOT account for disc id collisions *"

message_window_text_box = ScrolledText(message_window, width="50", height="16", wrap="word")
message_window_text_box.insert(tk.END, message_text)
message_window_text_box.config(state='disabled', background="#d9d9d9")
message_window_text_box.pack(side=tk.TOP, padx=20, pady=20)

message_window.focus_force()

close_button = tk.Button(message_window, text="Continue", command=close_message)

close_button.pack()

main_window.mainloop()
