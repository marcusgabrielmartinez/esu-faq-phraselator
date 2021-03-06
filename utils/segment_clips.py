import os
import argparse
import typing

from pydub import AudioSegment

def import_clips(files, directory: list, format: str) -> dict:
    clips = {}
    for filename in files:
        clips[filename] = AudioSegment.from_file(directory+'/'+filename, format=format, framerate=16000)
    
    return clips

def segment_clips(clips: dict, clip_length: int, output) -> dict:
    segmented = {}
    for filename, clip in clips.items():
        if not output:
            segmented.update({filename[:-4]+str(seg_clip[0])+'.wav': seg_clip[1] for seg_clip in enumerate(clip[::clip_length])})
        else:
            segmented.update({output+str(seg_clip[0])+'.wav': seg_clip[1] for seg_clip in enumerate(clip[::clip_length])})

    
    return segmented
    
def main(args):
    clips = import_clips(os.listdir(args.directory), args.directory, args.format)
    segmented = segment_clips(clips, int(args.clip_length)*1000, args.output)

    for filename, segment in segmented.items():
        with open(filename, 'wb') as sound:
            segment.export(sound, format='wav')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Segment audio clips into smaller segments of themselves.')
    parser.add_argument('--directory', '-d', default='./', help='Use this argument to specify the directory that contains the clips you want segmented. If not specified, the current directory is attempted.')
    parser.add_argument('--clip_length', '-c', default='10', help='Use this argument to specify the length of the output clips. Specify time in seconds. If not specified, the default is 10 seconds.')
    parser.add_argument('--format', '-f', default='mp3', help='Use this argument to specify the file format. mp3, wav, etc. Default is mp3.')
    parser.add_argument('--output', '-o', default=False)
    main(parser.parse_args())
