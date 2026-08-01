import os

def remove_master_mechanic(root_dir):
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
                    new_content = new_content.replace('expert mechanics', 'expert mechanics')
                    new_content = new_content.replace('expert mechanic', 'expert mechanic')
                    new_content = new_content.replace('certified mechanics', 'certified mechanics')
                    new_content = new_content.replace('certified mechanic', 'certified mechanic')
                    new_content = new_content.replace('Expert Mechanic', 'Expert Mechanic')
                    new_content = new_content.replace('Certified Mechanics', 'Certified Mechanics')

                    if content != new_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        replaced_files.append(filepath)
                        print(f"Updated: {filepath}")
                except Exception as e:
                    print(f"Skipped {filepath}: {e}")

    print(f"\nTotal files updated: {len(replaced_files)}")

if __name__ == '__main__':
    remove_master_mechanic(os.path.dirname(os.path.abspath(__file__)))
