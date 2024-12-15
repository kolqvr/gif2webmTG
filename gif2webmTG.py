import os
import shutil
import subprocess
from PIL import Image

def get_video_duration(video_path):
    """Gets the duration of a video using ffprobe."""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting duration for {video_path}: {e}")
        return None
    except ValueError:
        print(f"Could not parse duration for {video_path}")
        return None

def convert_gif_to_webm(gif_path, output_folder):
    """
    Converts a GIF file to a WEBM video meeting the specified requirements.

    Args:
        gif_path: Path to the input GIF file.
        output_folder: Path to the folder where the output WEBM will be saved.
    """

    try:
        # Get GIF info using Pillow
        with Image.open(gif_path) as img:
            duration = img.info.get('duration', 100)  # Default to 100ms per frame if not found
            frames = img.n_frames
            width, height = img.size

        # Calculate frame rate (limit to 30 FPS)
        fps = min(frames / (duration * frames / 1000), 30) 

        # Calculate duration in seconds
        total_duration = (duration * frames) / 1000 
        if total_duration > 3:
            print(f"Warning: {os.path.basename(gif_path)} exceeds 3 seconds. Trimming to 3 seconds.")
            fps = 3 / (duration * frames / 1000) * frames

        # Determine output dimensions (one side must be 512px)
        if width > height:
            new_width = 512
            new_height = int(height * (512 / width))
        else:
            new_height = 512
            new_width = int(width * (512 / height))

        # Construct output file name
        output_filename = os.path.splitext(os.path.basename(gif_path))[0] + ".webm"
        output_path = os.path.join(output_folder, output_filename)

        # Use ffmpeg to convert the GIF to WEBM
        ffmpeg_command = [
            "ffmpeg",
            "-i", gif_path,
            "-filter_complex", f"[0:v] scale={new_width}:{new_height}:flags=lanczos",
            "-c:v", "libvpx-vp9",
            "-b:v", "0",
            "-crf", "10",
            "-an",
            "-loop", "0",
            "-frames:v", str(int(fps * 3)),
            "-y",
            output_path
        ]
       
        subprocess.run(ffmpeg_command, check=True)
        print(f"Converted '{os.path.basename(gif_path)}' to '{output_filename}'")

    except (FileNotFoundError, Image.DecompressionBombError) as e:
        print(f"Error processing {os.path.basename(gif_path)}: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error during ffmpeg conversion of {os.path.basename(gif_path)}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred processing {os.path.basename(gif_path)}: {e}")

def optimize_webm_size_and_duration(webm_path, output_folder):
    """
    Optimizes a WEBM video to be 256 KB or less and trims it to 3 seconds if necessary.
    Moves all processed files (optimized or not) to the output folder.

    Args:
        webm_path: Path to the input WEBM file.
        output_folder: Path to the folder where the optimized WEBM will be saved.
    """
    original_size = os.path.getsize(webm_path)
    duration = get_video_duration(webm_path)

    output_filename = os.path.basename(webm_path)  # Use the original filename
    output_path = os.path.join(output_folder, output_filename)

    if original_size <= 256 * 1024 and (duration is None or duration <= 3):
        print(f"'{os.path.basename(webm_path)}' is within size and duration limits. Moving to output folder.")
        shutil.copy2(webm_path, output_path)  # Copy the file directly
        return  # Exit the function after moving

    # -- Optimization code (only runs if needed) --
    print(f"Optimizing '{os.path.basename(webm_path)}'...")

    try:
        with Image.open(webm_path) as img:
            width, height = img.size
    except Exception as e:
        print(f"Error getting dimensions for {webm_path}: {e}")
        width, height = 512, 512

    # Initial FFmpeg command
    ffmpeg_command = [
        "ffmpeg",
        "-i", webm_path,
    ]

    # Trim to 3 seconds if longer
    if duration is not None and duration > 3:
        ffmpeg_command.extend(["-t", "3"])

    # Optimization loop
    crf = 30  # Initial CRF
    while True:
        # Construct FFmpeg command with current CRF
        ffmpeg_command_with_crf = ffmpeg_command + [
            "-c:v", "libvpx-vp9",
            "-b:v", "0",  # Important for CRF mode
            "-crf", str(crf), # Correctly specify CRF as an option
            "-an",
            "-y",
            output_path
        ]
        
        subprocess.run(ffmpeg_command_with_crf, check=True)
        optimized_size = os.path.getsize(output_path)

        if optimized_size <= 256 * 1024:
            print(f"Successfully optimized '{os.path.basename(webm_path)}' to {optimized_size} bytes.")
            break
        elif crf >= 50:
            print(f"Warning: Could not optimize '{os.path.basename(webm_path)}' below 256 KB with CRF 50. Trying to reduce resolution...")
            # Fallback: Reduce resolution
            new_width = int(width * 0.8)  
            new_height = int(height * 0.8)
            ffmpeg_command_with_crf = [
                "ffmpeg",
                "-i", webm_path,
                "-filter:v", f"scale={new_width}:{new_height}",
                "-c:v", "libvpx-vp9",
                "-b:v", "0",
                "-crf", "35", # Reset CRF
                "-an",
                "-y",
                output_path
            ]
            subprocess.run(ffmpeg_command_with_crf, check=True)
            optimized_size = os.path.getsize(output_path)
            
            if optimized_size <= 256 * 1024:
                print(f"Successfully optimized '{os.path.basename(webm_path)}' to {optimized_size} bytes by reducing resolution.")
                break
            else:
                print(f"Error: Could not optimize '{os.path.basename(webm_path)}' below 256 KB even after reducing resolution.")
                break
        else:
            print(f"File size is {optimized_size} bytes (CRF {crf}). Increasing CRF...")
            crf += 5

def process_webm_files(input_folder, output_folder):
    """
    Processes all WEBM files in a folder, optimizing those over 256 KB.

    Args:
        input_folder: Path to the folder containing WEBM files.
        output_folder: Path to the folder where optimized WEBM files will be saved.
    """
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".webm"):
            webm_path = os.path.join(input_folder, filename)
            optimize_webm_size_and_duration(webm_path, output_folder)

def process_gifs_in_folder(input_folder, output_folder):
    """
    Processes all GIF files in a folder and converts them to WEBM.

    Args:
        input_folder: Path to the folder containing GIF files.
        output_folder: Path to the folder where the output WEBM files will be saved.
    """
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".gif"):
            gif_path = os.path.join(input_folder, filename)
            convert_gif_to_webm(gif_path, output_folder)

if __name__ == "__main__":
    input_folder = "gifs"  # Folder with the initial GIF files
    webm_output_folder = "webm_stickers"  # Folder for the converted WEBM files
    optimized_folder = "webm_stickers_optimized"  # Folder for the optimized WEBM files
    final_folder = "finished"  # Folder for the final, optimized WEBM files

    # Create required folders if they don't exist
    for folder in [webm_output_folder, optimized_folder, final_folder]:
        os.makedirs(folder, exist_ok=True)

    # Check for the "gifs" folder
    if not os.path.exists(input_folder):
        print("Error: You need to create a 'gifs' folder and put your GIF files inside it.")
    else:
        # 1. Convert GIFs to WEBM
        process_gifs_in_folder(input_folder, webm_output_folder)

        # 2. Optimize WEBM files (size and duration)
        process_webm_files(webm_output_folder, optimized_folder)

        # 3. Move all optimized WEBM files to the final folder
        for filename in os.listdir(optimized_folder):
            source_path = os.path.join(optimized_folder, filename)
            destination_path = os.path.join(final_folder, filename)
            shutil.move(source_path, destination_path)

        # 4. Delete the intermediate folders
        try:
            shutil.rmtree(webm_output_folder)  # Delete webm_stickers
            shutil.rmtree(optimized_folder)  # Delete webm_stickers_optimized
            print(f"Deleted intermediate folders: '{webm_output_folder}', '{optimized_folder}'")
        except OSError as e:
            print(f"Error deleting folders: {e}")

        print(f"All done! Check the '{final_folder}' folder for the optimized stickers.")
