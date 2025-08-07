import re

class SMDFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.nodes = []
        self.materials = set()
        self._parse_file()

    def _parse_file(self):
        section = None

        with open(self.filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Handle section transitions
            if line == 'nodes':
                section = 'nodes'
                i += 1
                continue
            elif line == 'skeleton':
                section = 'skeleton'
                i += 1
                continue
            elif line == 'triangles':
                section = 'triangles'
                i += 1
                continue
            elif line == 'end':
                section = None
                i += 1
                continue

            # Parse based on section
            if section == 'nodes':
                match = re.match(r'^(\d+)\s+"(.+?)"\s+(-?\d+)', line)
                if match:
                    node_id = int(match.group(1))
                    name = match.group(2)
                    parent_id = int(match.group(3))
                    self.nodes.append({
                        'id': node_id,
                        'name': name,
                        'parent': parent_id
                    })
            elif section == 'triangles':
                material_name = line.strip()
                self.materials.add(material_name)
                i += 3  # skip the next 3 lines (vertex data)
            i += 1
