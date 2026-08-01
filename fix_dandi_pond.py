import os

def replace_dandi_beach(root_dir):
    extensions = ('.py', '.jsx', '.js', '.json', '.html', '.md', '.css')
    replaced_files = []

    for root, dirs, files in os.walk(root_dir):
        if 'node_modules' in root or '.git' in root or 'dist' in root or '.system_generated' in root:
            continue
        for file in files:
            if file.endswith(extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    new_content = content
                    new_content = new_content.replace('Near Dandi Pond', 'Near Dandi Pond')
                    new_content = new_content.replace('Dandi Pond Road', 'Dandi Pond Road')
                    new_content = new_content.replace('Dandi Pond', 'Dandi Pond')
                    new_content = new_content.replace('dandi pond', 'dandi pond')
                    new_content = new_content.replace('Dandi pond', 'Dandi pond')

                    if content != new_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        replaced_files.append(filepath)
                        print(f"Updated: {filepath}")
                except Exception as e:
                    print(f"Skipped {filepath}: {e}")

    print(f"\nTotal files updated: {len(replaced_files)}")

if __name__ == '__main__':
    replace_dandi_beach(os.path.dirname(os.path.abspath(__file__)))
