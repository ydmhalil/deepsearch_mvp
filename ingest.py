import argparse
import json
import os
from tqdm import tqdm

from utils import iter_files, extract_text
from chunker_smart import SmartChunker


def main(source_dir: str, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    files = list(iter_files(source_dir))
    chunker = SmartChunker()
    
    with open(output_path, 'w', encoding='utf-8') as out:
        for path in tqdm(files, desc='Files'):
            text = extract_text(path)
            chunks = chunker.chunk_document(text, path)
            for c in chunks:
                record = {
                    'file_path': path,
                    'text': c['text'],
                    'meta': c['meta']
                }
                out.write(json.dumps(record, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Source folder to scan')
    parser.add_argument('--output', required=True, help='Output JSONL file for chunks')
    args = parser.parse_args()
    main(args.source, args.output)
