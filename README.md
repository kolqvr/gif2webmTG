# gif2webmTG
That is converter gif to webm (all of the required settings is applied to your gifs) used to convert gifs so you can upload it to "Stickers" bot in telegram.

## PC version  (gif2webmTG.py) :
How to Use and What to Install:
Install Python: If you don't have Python 3 installed, download and install it from the official Python website (https://www.python.org/downloads/). Make sure you check the box that says "Add Python to PATH" during installation.

Install Required Libraries:
Pillow: Open your command prompt or terminal and type:
pip install Pillow

FFmpeg:
Windows:
Go to the FFmpeg website: https://ffmpeg.org/download.html

Find a Windows build (e.g., from gyan.dev) and download it.
Extract the downloaded archive (e.g., using 7-Zip).

Add the bin folder inside the extracted FFmpeg folder to your system's PATH environment variable. (Search for "environment variables" in the Windows search bar, click "Edit the system environment variables", then click "Environment Variables...", find "Path" in the "System variables" list, select it, click "Edit...", then "New", and paste the path to the bin folder).

macOS:
If you have Homebrew installed, open your terminal and type:
brew install ffmpeg
If you don't have Homebrew, install it first: https://brew.sh/

Linux: Use your distribution's package manager. For example, on Ubuntu/Debian:
sudo apt-get update
sudo apt-get install ffmpeg

install one of the scripts (for mobile: and for pc: gif2webmTG.py)

Organize Folders:
Create a folder named gifs in the same directory where you saved the script. This is where you will put the GIF files you want to convert.
Place GIFs: Put all your GIF files into the gifs folder.

Run the Script:
Open your command prompt or terminal.
Navigate to the directory where you saved the script and the gifs folder using the cd command. For example:
cd C:\Users\YourName\Documents\StickerConverter

Run the script using:
python gif2webmTG.py
Check Output: After the script finishes, you will find the converted and optimized WEBM files in the finished folder. The webm_stickers and webm_stickers_optimized folders will also be created during the process.



## Mobile version (gif2webmTGm.sh):
Since we cannot use Python directly in Termux without some setup, we'll create a Bash script that utilizes ffmpeg (which is readily available in Termux), you can try to run the python script but it probably wouldn't work.

How to Use in Termux:
Install Termux: Install the Termux app from the F-Droid or Google Play Store.

Open Termux and Update:
pkg update && pkg upgrade

Install Required Packages:
pkg install ffmpeg imagemagick

Install bc (for floating-point calculations):
pkg install bc

Navigate to Storage:
Give Termux storage permissions. Go to your device's Settings -> Apps -> Termux -> Permissions -> Storage, and enable it.

In Termux, use the termux-setup-storage command. This will create a storage directory in your Termux home directory, with symbolic links to your device's internal storage. You can access it via:
cd /data/data/com.termux/files/home/storage/shared

Create the Script:
You can use a text editor like nano or vim in Termux to create the script:
nano converter.sh

Copy the entire bash script (converter.sh) above and paste it into the nano editor.

Save the file (Ctrl+O) and exit (Ctrl+X).

Make the Script Executable:
chmod +x converter.sh

Create gifs Folder:
mkdir gifs

Place GIFs: Put your GIF files into the gifs folder that you just created. You might need to use a file manager app on your Android device to copy files into the storage/shared directory (or a subdirectory within it) that Termux can access.

Run the Script:
./converter.sh

Check Output: After the script finishes, you will find the converted and optimized WEBM files in the finished folder. The webm_stickers and webm_stickers_optimized folders will be created and then deleted during the process.



### Q&A:
# Q: Do i need root to run that on mobile?
# A: No, you do not need root access to use this bash script in Termux. The script and the required tools (ffmpeg, imagemagick, bc) can all be installed and used within the regular, unrooted Termux environment.
