import heapq
class HuffmanNode:
    """
    Represents a node in the Huffman Tree.
    - char: The character (None for internal nodes).
    - weight: The frequency/weight of the character.
    - left/right: Pointers to child nodes.
    """
    def __init__(self, char, weight):
        self.char = char
        self.weight = weight
        self.left = None
        self.right = None
    # Defines the comparison rule for the priority queue (min-heap)
    def __lt__(self, other):
        return self.weight < other.weight
def build_huffman_tree(data):
    """
    Algorithm to construct the Huffman Tree.
    Matches the merging logic shown in the blue circles of the image.
    """
    # Create a forest of initial leaf nodes (the white boxes in the image)
    priority_queue = [HuffmanNode(char, weight) for char, weight in data.items()]
    heapq.heapify(priority_queue)
    # Iterate until only one root node remains (the '36' at the top)
    while len(priority_queue) > 1:
        # Pop the two nodes with the smallest weights
        left_child = heapq.heappop(priority_queue)
        right_child = heapq.heappop(priority_queue)
        # Create a new internal node (blue circle) with combined weight
        merged = HuffmanNode(None, left_child.weight + right_child.weight)
        merged.left = left_child
        merged.right = right_child
        # Push the merged node back into the queue
        heapq.heappush(priority_queue, merged)
    return priority_queue[0]
def generate_huffman_codes(root, current_code="", code_map=None):
    """
    Recursively traverses the tree to assign 0 (left) and 1 (right) to each character.
    """
    if code_map is None:
        code_map = {}
    if root is None:
        return code_map
    # If it's a leaf node, store the binary sequence
    if root.char is not None:
        code_map[root.char] = current_code
    generate_huffman_codes(root.left, current_code + "0", code_map)
    generate_huffman_codes(root.right, current_code + "1", code_map)
    return code_map
if __name__ == "__main__":
    # --- Data Input from the provided image ---
    # Weights (w) from the white leaf nodes
    frequency_data = {
        'e': 4,
        'a': 4,
        'i': 2,
        'u': 2,
        'o': 2,
        'h': 2,
        's': 2,
        'f': 3,
        'c': 1,
        'm': 1,
        'r': 1,
        'l': 1
    }
    # Build the Huffman tree
    huffman_root = build_huffman_tree(frequency_data)
    # Generate Huffman codes
    final_codes = generate_huffman_codes(huffman_root)
    # Display results
    print("Huffman Codes for each character:")
    for char, code in final_codes.items():
        print(f"Char: '{char}' -> Code: {code}")
    # Optional: demonstrate encoding a sample string
    sample_text = "aabbbc"
    encoded = ''.join(final_codes[ch] for ch in sample_text if ch in final_codes)
    print(f"\nEncoding of '{sample_text}': {encoded}")
