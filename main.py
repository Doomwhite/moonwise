import sqlite3
import argparse
from datetime import datetime
import os
import re

def format_timestamp(timestamp):
    """
    Convert a Unix timestamp (in milliseconds) to a human-readable date and time.
    """
    return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")

def format_note_for_obsidian(timestamp, original, note):
    """
    Format the note for Obsidian Markdown.
    """
    formatted_note = f"### {timestamp}\n"
    formatted_note += f"**Highlight:**\n{original}\n\n"
    if note and note.strip():
        formatted_note += f"**Comment:**\n{note}\n\n"
    formatted_note += "---\n"
    return formatted_note

def sanitize_filename(book_name):
    """
    Sanitize the book name to make it a valid filename.
    """
    # Replace problematic characters with underscores
    sanitized = re.sub(r'[\\/:*?"<>|]', '_', book_name)
    # Remove leading/trailing whitespace and truncate to a reasonable length
    return sanitized.strip()[:100]

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract notes from Moon+ Reader backup.')
    parser.add_argument('--db_path', type=str, required=True, help='Path to the mrbooks.db file.')
    args = parser.parse_args()

    # Get notes from db
    with sqlite3.connect(args.db_path) as db:
        cursor = db.cursor()
        cursor.execute('SELECT book, time, original, note, lastPosition FROM notes WHERE original != "";')
        notes = cursor.fetchall()
        print(f'Found {len(notes)} notes')

    # Group notes by book and sort by lastPosition
    books = {}
    for (book, time, original, note, lastPosition) in notes:
        if book not in books:
            books[book] = []
        formatted_time = format_timestamp(time)
        books[book].append((lastPosition, formatted_time, original, note))

    # Sort notes within each book by lastPosition
    for book in books:
        books[book].sort(key=lambda x: x[0])  # Sort by lastPosition (first element in the tuple)

    # Create a directory to store the files
    output_dir = "moon_reader_notes"
    os.makedirs(output_dir, exist_ok=True)

    # Save notes to separate files for each book
    for book, book_notes in books.items():
        # Sanitize the book name to create a valid filename
        sanitized_book_name = sanitize_filename(book)
        output_filename = f"{sanitized_book_name}.md"
        output_path = os.path.join(output_dir, output_filename)

        # Write notes to the file
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(f"# {book}\n\n")
            for (lastPosition, timestamp, original, note) in book_notes:
                output_file.write(format_note_for_obsidian(timestamp, original, note))
            output_file.write("\n")  # Add a newline at the end

        print(f"Saved notes for '{book}' to {output_path}")

    print(f"All notes saved to the directory '{output_dir}'")
