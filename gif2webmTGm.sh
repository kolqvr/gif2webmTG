#!/bin/bash

# Folder names
input_folder="gifs"
webm_output_folder="webm_stickers"
optimized_folder="webm_stickers_optimized"
final_folder="finished"

# Function to get video duration using ffprobe
get_video_duration() {
  ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$1"
}

# Function to convert GIF to WEBM
convert_gif_to_webm() {
  local gif_path="$1"
  local output_folder="$2"
  local output_filename=$(basename "$gif_path" .gif).webm
  local output_path="$output_folder/$output_filename"

  # Get GIF info using identify (ImageMagick)
  duration=$(identify -format "%T" "$gif_path" | awk '{s+=$1} END {print s/100}') # Duration per frame in 1/100 s
  frames=$(identify -format "%n" "$gif_path")
  width=$(identify -format "%w" "$gif_path")
  height=$(identify -format "%h" "$gif_path")

  # Calculate frame rate (limit to 30 FPS)
  fps=$(echo "scale=2; if ($frames / ($duration * $frames / 1000) < 30) $frames / ($duration * $frames / 1000) else 30" | bc)

  # Calculate duration and trim if necessary
  total_duration=$(echo "scale=2; $duration * $frames / 1000" | bc)
  if (( $(echo "$total_duration > 3" | bc -l) )); then
    echo "Warning: $gif_path exceeds 3 seconds. Trimming to 3 seconds."
    fps=$(echo "scale=2; 3 / ($duration * $frames / 1000) * $frames" | bc)
  fi

  # Determine output dimensions (one side must be 512px)
  if (( $(echo "$width > $height" | bc -l) )); then
    new_width=512
    new_height=$(echo "scale=0; $height * 512 / $width" | bc)
  else
    new_height=512
    new_width=$(echo "scale=0; $width * 512 / $height" | bc)
  fi

  # Use ffmpeg to convert the GIF to WEBM
  ffmpeg -i "$gif_path" -filter_complex "scale=$new_width:$new_height:flags=lanczos" -c:v libvpx-vp9 -b:v 0 -crf 10 -an -loop 0 -frames:v $(echo "$fps * 3" | bc) -y "$output_path"

  if [[ $? -eq 0 ]]; then
    echo "Converted '$gif_path' to '$output_filename'"
  else
    echo "Error during ffmpeg conversion of $gif_path"
  fi
}

# Function to optimize WEBM size and duration
optimize_webm_size_and_duration() {
  local webm_path="$1"
  local output_folder="$2"
  local output_filename=$(basename "$webm_path")
  local output_path="$output_folder/$output_filename"

  original_size=$(stat -c%s "$webm_path")
  duration=$(get_video_duration "$webm_path")

  if (( $(echo "$original_size <= 256 * 1024 && ($duration <= 3 || $duration == \"\")" | bc -l) )); then
    echo "'$webm_path' is within size and duration limits. Moving to output folder."
    cp -p "$webm_path" "$output_path" # Use cp -p to preserve metadata
    return
  fi

  # -- Optimization code (only runs if needed) --
  echo "Optimizing '$webm_path'..."

  # Get video dimensions using ffprobe
  width=$(ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "$webm_path")
  height=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "$webm_path")

  # Initial FFmpeg command
  ffmpeg_command=(ffmpeg -i "$webm_path")

  # Trim to 3 seconds if longer
  if (( $(echo "$duration > 3" | bc -l) )); then
    ffmpeg_command+=("-t" "3")
  fi

  # Optimization loop
  crf=30
  while true; do
    # Construct FFmpeg command with current CRF
    ffmpeg_command_with_crf=("${ffmpeg_command[@]}")  # Make a copy of the array
    ffmpeg_command_with_crf+=("-c:v" "libvpx-vp9" "-b:v" "0" "-crf" "$crf" "-an" "-y" "$output_path")

    "${ffmpeg_command_with_crf[@]}"  # Run FFmpeg command

    optimized_size=$(stat -c%s "$output_path")

    if (( $(echo "$optimized_size <= 256 * 1024" | bc -l) )); then
      echo "Successfully optimized '$webm_path' to $optimized_size bytes."
      break
    elif (( $(echo "$crf >= 50" | bc -l) )); then
      echo "Warning: Could not optimize '$webm_path' below 256 KB with CRF 50. Trying to reduce resolution..."
      # Fallback: Reduce resolution
      new_width=$(echo "scale=0; $width * 0.8" | bc)
      new_height=$(echo "scale=0; $height * 0.8" | bc)
      ffmpeg_command_with_crf=("ffmpeg" "-i" "$webm_path" "-filter:v" "scale=$new_width:$new_height" "-c:v" "libvpx-vp9" "-b:v" "0" "-crf" "35" "-an" "-y" "$output_path")

      "${ffmpeg_command_with_crf[@]}"  # Run FFmpeg command

      optimized_size=$(stat -c%s "$output_path")

      if (( $(echo "$optimized_size <= 256 * 1024" | bc -l) )); then
        echo "Successfully optimized '$webm_path' to $optimized_size bytes by reducing resolution."
        break
      else
        echo "Error: Could not optimize '$webm_path' below 256 KB even after reducing resolution."
        break
      fi
    else
      echo "File size is $optimized_size bytes (CRF $crf). Increasing CRF..."
      crf=$((crf + 5))
    fi
  done
}

# Create required folders
for folder in "$webm_output_folder" "$optimized_folder" "$final_folder"; do
  mkdir -p "$folder"
done

# Check for the "gifs" folder
if [ ! -d "$input_folder" ]; then
  echo "Error: You need to create a '$input_folder' folder and put your GIF files inside it."
else
  # 1. Convert GIFs to WEBM
  find "$input_folder" -maxdepth 1 -name "*.gif" -print0 | while IFS= read -r -d $'\0' gif; do
    convert_gif_to_webm "$gif" "$webm_output_folder"
  done

  # 2. Optimize WEBM files (size and duration)
  find "$webm_output_folder" -maxdepth 1 -name "*.webm" -print0 | while IFS= read -r -d $'\0' webm; do
    optimize_webm_size_and_duration "$webm" "$optimized_folder"
  done

  # 3. Move optimized WEBM files to the final folder
  find "$optimized_folder" -maxdepth 1 -name "*.webm" -print0 | while IFS= read -r -d $'\0' webm; do
    mv -v "$webm" "$final_folder/"
  done

  # 4. Delete the intermediate folders
  rm -rv "$webm_output_folder" "$optimized_folder"

  echo "All done! Check the '$final_folder' folder for the optimized stickers."
fi
