#
"""
Utility functions for the FoodChatbot crawler.

Includes: file combining, cleaning, deduplication, atomic file writing, URL loading, blacklist filtering.
Optimized for large text/link file processing.

Author: FoodChatbot Team
"""

from pathlib import Path          
from typing import Set
import logging
import os      


def combine_files(source_dir: str, destination_file: str):
    """
    Combine all unique lines from files named file*.txt in subdirectories of source_dir into destination_file.

    Args:
        source_dir: Directory containing subdirectories with files to combine.
        destination_file: Output file to write unique lines to.

    Returns:
        None
    """
    import os
    dirs = os.listdir(source_dir)
    unique_lines = set()
    for dir_name in dirs:
        dir_path = os.path.join(source_dir, dir_name)
        if os.path.isdir(dir_path):
            for file_name in os.listdir(dir_path):
                if file_name.startswith("file") and file_name.endswith(".txt"):
                    file_path = os.path.join(dir_path, file_name)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                if line.strip() not in unique_lines:
                                    unique_lines.add(line.strip())
                                    with open(destination_file, 'a', encoding='utf-8') as dest_file:
                                        dest_file.write(line.strip() + '\n')
    clean_up(destination_file)
                                        
def clean_up(target: str):
    """
    Clean up a file by removing lines that do not match recipe URL patterns or contain unwanted substrings.

    Args:
        target: Path to the file to clean.

    Returns:
        None
    """
    with open(target, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(target, 'w', encoding='utf-8') as f:
        for line in lines:
            if len(line.split('/')) > 5:
                continue  
            if not "https://therecipecritic.com/" in line:
                continue
            if "weekly-meal-" in line:
                continue
            if "-recipes" in line:
                continue
            if "#" in line:
                continue
            if line.strip():
                f.write(line)
                
                
def remove_duplicates(target: str):
    """
    Remove duplicate lines from a file, sort them, and overwrite the file.

    Args:
        target: Path to the file to deduplicate.

    Returns:
        None
    """
    with open(target, "r", encoding='utf-8') as f:
        lines = f.readlines()
    unique_lines = list(set(line.strip() for line in lines))
    unique_lines.sort()
    with open(target, "w", encoding='utf-8') as f:
        for line in unique_lines:
            f.write(line + "\n")
                
def safe_write_lines(path: Path, lines) -> None:
    """
    Atomically write lines to a file (write to .tmp then rename to target).

    Args:
        path: Path to the output file.
        lines: Iterable of lines to write.

    Returns:
        None
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(f"{line}\n")
    tmp.replace(path)

def load_url_file(target: str) -> Set[str]:
    """
    Load URLs from a file, one per line, into a set.

    Args:
        target: Path to the file containing URLs.

    Returns:
        Set of URLs (str).
    """
    result = set()
    if Path(target).exists():
        with open(target, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if url:
                    result.add(url)
    return result

def filter_blacklist(urls: Set[str], blacklist: Set[str], output_file: str) -> Set[str]:
    """
    Filter out URLs that are present in the blacklist and save the result to a file.

    Args:
        urls: Set of URLs to filter.
        blacklist: Set of URLs to exclude.
        output_file: Path to the output file to save filtered URLs.

    Returns:
        Set of filtered URLs (not in blacklist).
    """
    result = set()
    for url in urls:
        if url not in blacklist:
            result.add(url)
    # save to file
    with open(output_file, "w", encoding="utf-8") as f:
        for url in sorted(result):
            f.write(url + "\n")
    return result