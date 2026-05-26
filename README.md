# Video pre-processing

Suite of utils to prepare metadata files, and perform video pre-processing based on metadata.

Metadata files determine input file names, target video excerpt timestamps to be extracted, and corresponding output file names.
Video pre-processing uses FFmpeg to convert, rotate, stitch, merge, etc. video excerpts to generate video files with only targeted content prepared for expert analysis.

# Usage

To prepare the metadata files, make sure the original metadata files are placed in
`/metadata/original`.

Then run:

```bash
python cleaning.py
```

The `cleaning.py` script will generate the cleaned metadata files in `/metadata/cleaned` per targeted date.

Then run:

```bash
python cleaning.py \
  --input_data /path/to/raw/video_folder \
  --local /path/to/local/directory \
  --meta_data /path/to/metadata/cleaned \
  --target_date 01JAN2026 \
  --rotate False \
  --experiment project_name \
  --output_data /path/to/processed
```

### Arguments

| Argument           | Description                                                           |
| ------------------ | --------------------------------------------------------------------- |
| `--input_data`     | Path to the parent directory containing the data to process           |
| `--local`          | Path to local directory to save logs, find metadata, save temp files  |
| `--meta_data`      | Name of folder in /metadata/ to retrieve files to process.            |
| `--target_date`    | Target day in format DDMMMYYYY (e.g. 13SEP2024) to process            |
| `--rotate`         | Enable rotate videos in 90 degrees                                    |
| `--experiment`     | Experiment name to process the data for                               |
| `--output_data`    | PATH to a directory for outputting the files                          |
