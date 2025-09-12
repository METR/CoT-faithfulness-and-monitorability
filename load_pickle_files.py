#!/usr/bin/env python3

import pathlib
import pickle
import sys


def load_and_print_pickle_files(directory_path):
    """Load and print all pickle files in the specified directory."""
    directory = pathlib.Path(directory_path)
    
    if not directory.exists():
        print(f"Directory {directory_path} does not exist")
        return
    
    if not directory.is_dir():
        print(f"{directory_path} is not a directory")
        return
    
    files_processed = 0
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            try:
                # print(f"Loading file: {file_path.name}")
                
                with open(file_path, 'rb') as f:
                    _, output = pickle.load(f)
                
                if len(output.completion) == 0 or len(output.choices) == 0 or len(output.choices[0].message.content) == 0:
                    print(f"File {file_path.name} has an empty completion")
                
                files_processed += 1
                
            except Exception as e:
                print(f"Error loading {file_path.name}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Total files processed: {files_processed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    directory = "/home/ec2-user/.cache/inspect_ai/generate/openai/o4-mini-2025-04-16"
    
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    load_and_print_pickle_files(directory) 