# AI-BEGIN
# src/numeric_core/bits.py
# Constraint-compliant bit utilities (no int(.., base), no hex(), no format(), no shifts).
# We treat bits as lists of {0,1}. Hex helpers use manual nibble lookup tables.

HEX_TO_NIBBLE = {
    '0':[0,0,0,0],'1':[0,0,0,1],'2':[0,0,1,0],'3':[0,0,1,1],
    '4':[0,1,0,0],'5':[0,1,0,1],'6':[0,1,1,0],'7':[0,1,1,1],
    '8':[1,0,0,0],'9':[1,0,0,1],'A':[1,0,1,0],'B':[1,0,1,1],
    'C':[1,1,0,0],'D':[1,1,0,1],'E':[1,1,1,0],'F':[1,1,1,1],
    'a':[0,0,0,0],'b':[0,0,0,1],'c':[0,0,1,0],'d':[0,0,1,1],  # placeholder; we normalize to upper later
}

# Fix lowercase mapping properly (above 'a'..'d' were placeholders). Let's generate lowercase map.
for k,v in list(HEX_TO_NIBBLE.items()):
    pass
# Overwrite with correct full map:
HEX_TO_NIBBLE = {
    **{h:HEX_TO_NIBBLE.get(h, [0,0,0,0]) for h in '0123456789ABCDEF'},
    **{h.lower():HEX_TO_NIBBLE.get(h, [0,0,0,0]) for h in '0123456789ABCDEF'},
}
# Re-assign proper values:
HEX_TO_NIBBLE.update({
    '0':[0,0,0,0],'1':[0,0,0,1],'2':[0,0,1,0],'3':[0,0,1,1],
    '4':[0,1,0,0],'5':[0,1,0,1],'6':[0,1,1,0],'7':[0,1,1,1],
    '8':[1,0,0,0],'9':[1,0,0,1],'A':[1,0,1,0],'B':[1,0,1,1],
    'C':[1,1,0,0],'D':[1,1,0,1],'E':[1,1,1,0],'F':[1,1,1,1],
    'a':[0,0,0,0],'b':[0,0,0,1],'c':[0,0,1,0],'d':[0,0,1,1],
    'e':[0,1,0,0],'f':[0,1,0,1],  # will fix below
})
# Correct lowercase by mirroring uppercase precisely:
for u,l in zip('0123456789ABCDEF', '0123456789abcdef'):
    HEX_TO_NIBBLE[l] = HEX_TO_NIBBLE[u]

NIBBLE_TO_HEX = {
    (0,0,0,0):'0',(0,0,0,1):'1',(0,0,1,0):'2',(0,0,1,1):'3',
    (0,1,0,0):'4',(0,1,0,1):'5',(0,1,1,0):'6',(0,1,1,1):'7',
    (1,0,0,0):'8',(1,0,0,1):'9',(1,0,1,0):'A',(1,0,1,1):'B',
    (1,1,0,0):'C',(1,1,0,1):'D',(1,1,1,0):'E',(1,1,1,1):'F',
}

def zeros(n):
    return [0]*n

def ones(n):
    return [1]*n

def pad_to_width(bits, width, pad_bit=0):
    if len(bits) >= width:
        return bits[-width:]
    return [pad_bit]*(width-len(bits)) + bits

def from_hex_string(s, width=None):
    """Convert hex string like '0xDEADBEEF' or 'DEAD_BEEF' to bit list.
    No use of int()/bin()/format()."""
    # strip prefixes/underscores/spaces
    cleaned = []
    for ch in s:
        if ch in 'xX_ ':
            continue
        cleaned.append(ch)
    if len(cleaned) >= 2 and cleaned[0]=='0' and (cleaned[1] in 'xX'):
        cleaned = cleaned[2:]
    # Build bits
    bits = []
    for ch in cleaned:
        nib = HEX_TO_NIBBLE.get(ch)
        if nib is None:
            raise ValueError('Invalid hex char: '+ch)
        bits.extend(nib)
    if width is not None:
        bits = pad_to_width(bits, width, pad_bit=0)
    return bits

def to_hex_string(bits, group=4, prefix='0x', width_multiple=8):
    """Pretty hex from bits using nibble lookup. Zero-pads to width_multiple nibbles (default 8=32 bits)."""
    n = len(bits)
    # pad to multiple of 4
    pad = (4 - (n % 4)) % 4
    work = [0]*pad + bits[:]
    # group nibbles
    hex_chars = []
    for i in range(0, len(work), 4):
        nib = tuple(work[i:i+4])
        hex_chars.append(NIBBLE_TO_HEX[nib])
    # ensure minimum width
    if width_multiple is not None:
        while len(hex_chars) < width_multiple:
            hex_chars.insert(0,'0')
    # optional underscore grouping (every 8 hex chars => 32 bits)
    out = ''.join(hex_chars)
    return prefix + out

def pretty_bin(bits, group=4, byte_group=8):
    """Return grouped binary string like 00000000_00000000_..."""
    s = ''.join('1' if b else '0' for b in bits)
    # group every 4
    out = []
    for i,ch in enumerate(s):
        out.append(ch)
        if (i+1)%4==0 and (i+1) != len(s):
            if (i+1)%byte_group==0:
                out.append('_')
    return ''.join(out)

def sign_extend(bits, width):
    sign = bits[0] if bits else 0
    return [sign]*(width-len(bits)) + bits

def zero_extend(bits, width):
    return [0]*(width-len(bits)) + bits
# AI-END
