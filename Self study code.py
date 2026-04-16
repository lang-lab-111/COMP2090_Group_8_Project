import heapq
from collections import Counter

# 1. Node class definition
class Node:
    def __init__(self, char, freq):
        self.char = char      # Leaf nodes have a character, internal nodes have None
        self.freq = freq
        self.left = None
        self.right = None

    # Make nodes comparable in heap (by frequency)
    def __lt__(self, other):
        return self.freq < other.freq

# 2. Build Huffman tree
def build_huffman_tree(text):
    # Count frequencies
    freq = Counter(text)
    # Create heap of leaf nodes
    heap = [Node(char, f) for char, f in freq.items()]
    heapq.heapify(heap)

    # Repeatedly merge the two smallest nodes
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        # Internal node: char=None, frequency = sum of both
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    # Return root of the tree
    return heap[0]

# 3. Generate codebook from tree (recursive)
def build_codes(node, prefix="", codebook={}):
    if node is None:
        return
    # Leaf node: record character code
    if node.char is not None:
        codebook[node.char] = prefix
    else:
        build_codes(node.left, prefix + "0", codebook)
        build_codes(node.right, prefix + "1", codebook)
    return codebook

# 4. Compress text -> binary string
def compress(text, codebook):
    return ''.join(codebook[ch] for ch in text)

# 5. Decompress binary string -> original text
def decompress(compressed_bits, root):
    result = []
    node = root
    for bit in compressed_bits:
        # Move along the tree
        node = node.left if bit == '0' else node.right
        # Reached a leaf node
        if node.char is not None:
            result.append(node.char)
            node = root   # Go back to root for next character
    return ''.join(result)

# ========== Demo ==========
if __name__ == "__main__":
    # Original text (feel free to modify)
    text = "this is an example for huffman tree"
    print(f"Original text: {text}")
    print(f"Original length: {len(text)} characters, occupies {len(text) * 8} bits (assuming ASCII)")

    # Build tree and generate codes
    tree_root = build_huffman_tree(text)
    codes = build_codes(tree_root, "", {})

    print("\nHuffman code table:")
    for ch, code in sorted(codes.items(), key=lambda x: len(x[1])):
        print(f"  '{ch}': {code} (length {len(code)})")

    # Compress
    compressed_bits = compress(text, codes)
    print(f"\nCompressed huffman code string: {compressed_bits[:50]}..." if len(compressed_bits) > 50 else compressed_bits)
    print(f"Compressed length: {len(compressed_bits)} bits")

    # Decompress and verify
    decompressed_text = decompress(compressed_bits, tree_root)
    print(f"\nDecompressed result: {decompressed_text}")
    print(f"Decompression correct: {decompressed_text == text}")

    # Calculate compression ratio
    original_bits = len(text) * 8
    compressed_bits_len = len(compressed_bits)
    print(f"\nCompression ratio: {compressed_bits_len}/{original_bits} = {compressed_bits_len/original_bits:.2%}")
