# KLEE Failure Analysis for lodepng.c

## Overview

This document identifies 6 case studies where KLEE (a symbolic execution engine) would fail or struggle when generating test values for `lodepng.c` (LodePNG version 20221108) using a driver code. Each case study provides detailed code references and explains the root cause of failure.

---

## Case Study 1: CRC32 and Adler32 Checksum Constraints (Solver Infeasibility)

**Core Problem**: KLEE's SMT solver cannot practically solve the non-linear algebraic relationships in checksum computations.

**CRC32** (`lodepng.c:2318-2325`):
```c
unsigned lodepng_crc32(const unsigned char* data, size_t length) {
  unsigned r = 0xffffffffu;
  for(i = 0; i < length; ++i) {
    r = lodepng_crc32_table[(r ^ data[i]) & 0xffu] ^ (r >> 8u);
  }
  return r ^ 0xffffffffu;
}
```
When `data[i]` is symbolic, the expression `(r ^ data[i]) & 0xff` is used as an **array index** into `lodepng_crc32_table` (256 entries, lines 2282-2315). Each iteration, KLEE must fork up to 256 ways (one per possible table index). Over `length` iterations, this creates **256^length** potential paths. After computing the CRC, the decoder verifies it matches the CRC embedded in the chunk:

At `lodepng.c:4889-4891`:
```c
if(!state->decoder.ignore_crc && !unknown) {
    if(lodepng_chunk_check_crc(chunk)) { state->error = 57; break; };
}
```

And at `lodepng.c:2402-2408`, `lodepng_chunk_check_crc` compares the computed CRC against the stored value. For KLEE to generate a valid PNG, it must craft symbolic bytes such that the CRC computation (through a chain of table lookups) produces a specific 32-bit value. This is essentially asking the SMT solver to invert a CRC32 function -- a constraint that is **non-linear and practically unsolvable** for Z3/STP.

**Adler32** suffers the same issue at `lodepng.c:2105-2108`:
```c
unsigned ADLER32 = lodepng_read32bitInt(&in[insize - 4]);
unsigned checksum = adler32(out->data, (unsigned)(out->size));
if(checksum != ADLER32) return 58;
```
The Adler32 computation (lines 2042-2060) involves modular arithmetic (`s1 %= 65521u; s2 %= 65521u`) on accumulated sums of decompressed data. KLEE would need to simultaneously solve for: (a) valid compressed data that decompresses correctly, and (b) the decompressed output whose Adler32 matches the 4 bytes at the end of the stream. This creates a **circular dependency** between constraints.

**KLEE Failure Mode**: Solver timeout or inability to generate inputs that pass checksum verification. Only paths returning error code 57 or 58 would be explored.

---

## Case Study 2: Path Explosion in Huffman Decoding (inflateHuffmanBlock)

**Core Problem**: The deflate decompression loop creates an exponential number of symbolic execution paths.

The main decompression loop at `lodepng.c:1160-1243`:
```c
while(!error && !done) {
    ensureBits32(reader, 30);
    code_ll = huffmanDecodeSymbol(reader, &tree_ll);
    if(code_ll <= 255) {          // Branch 1: literal byte
        ...
        code_ll = huffmanDecodeSymbol(reader, &tree_ll);
    }
    if(code_ll <= 255) { ... }     // Branch 2: another literal
    else if(code_ll >= 257 && code_ll <= 285) {  // Branch 3: length/distance
        length = LENGTHBASE[code_ll - 257];
        ...
        code_d = huffmanDecodeSymbol(reader, &tree_d);
        if(code_d > 29) { ... }    // Branch 4: invalid distance
        distance = DISTANCEBASE[code_d];
        ...
    } else if(code_ll == 256) {    // Branch 5: end code
        done = 1;
    } else {                       // Branch 6: invalid
        error = 16;
    }
}
```

At `huffmanDecodeSymbol` (lines 978-991), the function reads bits from symbolic input, indexes into `codetree->table_len` and `codetree->table_value` with a symbolic `code` value. The table has `1 << FIRSTBITS = 512` entries (FIRSTBITS=9, line 562). Each call creates hundreds of potential branches through the table lookups. The `if(l <= FIRSTBITS)` branch on line 982 determines single-table vs. two-table lookup.

**Each iteration** of the while loop at line 1160 creates at minimum 6 top-level branches (literal, literal-literal, length/distance, end code, invalid code, out-of-bounds). With symbolic compressed data, the loop iteration count is itself symbolic (it terminates when code 256 is encountered). For even a tiny 4x4 image, the decompressed data would be ~48+ bytes, requiring many loop iterations.

The **path explosion** is multiplicative: if each iteration creates ~6 top-level paths and the loop runs N times, the total path count is O(6^N). For any non-trivial image, KLEE would exhaust memory or time before exploring meaningful paths.

**KLEE Failure Mode**: Path explosion causing state exhaustion; only trivially short compressed streams would be fully explored.

---

## Case Study 3: Dynamic Huffman Tree Construction from Symbolic Input (getTreeInflateDynamic)

**Core Problem**: The dynamic Huffman tree must be constructed from symbolic bit-level values, creating deeply nested constraints that compound through multiple dependent stages.

At `lodepng.c:1009-1140`, `getTreeInflateDynamic` reads the dynamic Huffman tree structure from the compressed stream:

**Stage 1** - Read header values (lines 1026-1030):
```c
HLIT  = readBits(reader, 5) + 257;   // 257-288
HDIST = readBits(reader, 5) + 1;     // 1-32
HCLEN = readBits(reader, 4) + 4;     // 4-19
```
These three symbolic values determine the structure of everything that follows. HLIT has 32 possible values, HDIST has 32, HCLEN has 16 -- already 32 x 32 x 16 = **16,384 combinations** just from the header.

**Stage 2** - Read code length code lengths (lines 1042-1048):
```c
for(i = 0; i != HCLEN; ++i) {
    ensureBits9(reader, 3);
    bitlen_cl[CLCL_ORDER[i]] = readBits(reader, 3);
}
```
HCLEN is symbolic (4-19), so the loop bound is symbolic. Each `readBits(reader, 3)` reads 3 symbolic bits giving 8 possible values. For HCLEN=19 iterations, this creates 8^19 potential combinations of code lengths.

**Stage 3** - Build the code length tree and use it to decode the literal/distance trees (lines 1050-1121). The `HuffmanTree_makeFromLengths` call at line 1050 processes the symbolic `bitlen_cl` array through `HuffmanTree_makeFromLengths2` (lines 690-724), which generates Huffman codes and builds a lookup table. The tree construction involves loops with symbolic bounds and array accesses at symbolic indices (e.g., `++blcount[tree->lengths[bits]]` at line 704). Each of these creates symbolic index expressions.

**Stage 4** - The constructed tree is then used to decode the literal/length and distance code lengths (lines 1062-1121), where `huffmanDecodeSymbol` is called with a tree whose structure is itself symbolic. This creates a cascade: symbolic input -> symbolic tree structure -> symbolic symbol decoding -> symbolic output.

**KLEE Failure Mode**: The compound symbolic constraints from these four stages create expressions too complex for the solver. KLEE would fork excessively at Stage 2 and never reach Stage 4 in any meaningful capacity.

---

## Case Study 4: Zlib Header + PNG Magic Byte Multi-Constraint Satisfaction

**Core Problem**: KLEE must simultaneously satisfy a cascade of interdependent format-level constraints across multiple layers of the PNG format.

To reach any meaningful decoding logic, the symbolic input must satisfy these constraints **in sequence**:

**Layer 1 - PNG Signature** (`lodepng.c:3958-3960`):
```c
if(in[0] != 137 || in[1] != 80 || in[2] != 78 || in[3] != 71
   || in[4] != 13 || in[5] != 10 || in[6] != 26 || in[7] != 10)
```
Fixes bytes 0-7 to exact values. This alone is solvable.

**Layer 2 - IHDR chunk** (lines 3962-3993):
- Bytes 8-11: chunk length must equal 13 (`lodepng_chunk_length(in + 8) != 13`)
- Bytes 12-15: chunk type must be "IHDR" (`lodepng_chunk_type_equals(in + 8, "IHDR")`)
- Bytes 16-19: width, read as big-endian 32-bit (`lodepng_read32bitInt(&in[16])`) -- must be non-zero (line 3984)
- Bytes 20-23: height -- must be non-zero
- Byte 24: bitdepth -- must be valid for colortype
- Byte 25: colortype -- must be one of {0,2,3,4,6} (checked by `checkColorValidity`, lines 2534-2545)
- Byte 26: compression method must be 0
- Byte 27: filter method must be 0
- Byte 28: interlace method must be 0 or 1
- Bytes 29-32: CRC of bytes 12-28 must match (unless `ignore_crc`)

**Layer 3 - Chunk traversal** (lines 4775-4894):
The main chunk parsing loop uses `lodepng_chunk_type_equals` to compare 4 symbolic bytes against string constants ("IDAT", "IEND", "PLTE", etc.) -- that's up to **15+ string comparisons** per chunk iteration, each branching. The chunk type bytes are at `chunk[4..7]`, and each comparison creates 2 paths.

**Layer 4 - Zlib header inside IDAT** (lines 2079-2100):
```c
if((in[0] * 256 + in[1]) % 31 != 0) return 24;
CM = in[0] & 15;     // must be 8
CINFO = (in[0] >> 4) & 15;  // must be <= 7
FDICT = (in[1] >> 5) & 1;   // must be 0
```
The `% 31 == 0` constraint is a modular arithmetic constraint on two symbolic bytes. Combined with `CM == 8`, this means `in[0]` must have its low nibble equal to 8 (so `in[0]` is one of `0x08, 0x18, 0x28, 0x38, 0x48, 0x58, 0x68, 0x78`), and `in[1]` must satisfy `(in[0] * 256 + in[1]) % 31 == 0` AND `(in[1] >> 5) & 1 == 0`.

**KLEE Failure Mode**: While each individual constraint is solvable, the **depth of the constraint chain** means KLEE must navigate through all layers sequentially. The combination of exact-byte constraints, bitfield constraints, modular arithmetic, and CRC verification creates a constraint system where the solver spends enormous time on satisfiability queries. Most KLEE runs would only explore early rejection paths (error codes 28, 94, 29, 93, 37, etc.) and never reach actual image decompression.

---

## Case Study 5: LZ77 Hash Chain Traversal with Symbolic Data (encodeLZ77)

**Core Problem**: The LZ77 string matching algorithm involves data-dependent control flow through hash chains, creating paths proportional to input size squared.

The `encodeLZ77` function (`lodepng.c:1492-1639`) performs string matching using hash chains. Key problems for KLEE:

**Hash computation** (lines 1443-1460):
```c
static unsigned getHash(const unsigned char* data, size_t size, size_t pos) {
    result ^= ((unsigned)data[pos + 0] << 0u);
    result ^= ((unsigned)data[pos + 1] << 4u);
    result ^= ((unsigned)data[pos + 2] << 8u);
    return result & HASH_BIT_MASK;  // & 65535
}
```
When `data` is symbolic, the hash value is a symbolic 16-bit expression. This is used to index `hash->head[hashval]` at line 1476, creating up to **65,536 possible array index paths**.

**String matching loop** (lines 1544-1588):
```c
for(;;) {
    if(chainlength++ >= maxchainlength) break;
    ...
    while(foreptr != lastptr && *backptr == *foreptr) {
        ++backptr; ++foreptr;
    }
    current_length = (unsigned)(foreptr - &in[pos]);
    ...
    if(hashpos == hash->chain[hashpos]) break;
    hashpos = hash->chain[hashpos];
    if(hash->val[hashpos] != (int)hashval) break;
}
```
The inner `while` loop (line 1563) compares symbolic bytes one at a time. Each byte comparison `*backptr == *foreptr` creates a fork. With `maxchainlength` potentially up to 32768 (line 1498), and each chain link involving byte-by-byte comparison up to 258 bytes (MAX_SUPPORTED_DEFLATE_LENGTH), a single position in the outer loop can generate **maxchainlength x 258 = ~8.4 million** potential forks.

**Lazy matching** (lines 1590-1611) adds another dimension: it defers the encoding decision to compare the current match with the next position's match, doubling the effective exploration.

The outer `for(pos = inpos; pos < insize; ++pos)` at line 1519 iterates over every byte, so the total fork count scales as **O(insize x chainlength x match_length)**.

**KLEE Failure Mode**: State explosion from the triple-nested loop structure. Even for tiny inputs (say 20 bytes), the hash chain traversal and byte-by-byte comparison create thousands of states per input byte.

---

## Case Study 6: PNG Scanline Filter Reconstruction with Data Dependencies (unfilterScanline)

**Core Problem**: Filter types 3 (Average) and 4 (Paeth) create sequential data dependencies where each output byte depends on previously computed symbolic values, causing symbolic expression sizes to grow exponentially.

The `unfilterScanline` function at `lodepng.c:4006-4134` reconstructs pixel data by reversing PNG filters. The `filterType` byte itself is symbolic (read from `in[inindex]` at line 4156), causing KLEE to fork into 5 paths (types 0-4) **per scanline**.

**Filter Type 1 (Sub)** (lines 4022-4026):
```c
for(i = bytewidth; i != length; ++i, ++j)
    recon[i] = scanline[i] + recon[j];
```
`recon[i]` depends on `recon[j]` (where `j = i - bytewidth`). If `scanline` is symbolic, after N bytes, `recon[N]` is an expression involving the **sum of N/bytewidth symbolic variables**. The expression tree grows linearly.

**Filter Type 4 (Paeth)** (lines 4076-4129) is worse. Each byte calls `paethPredictor` (lines 3879-3886):
```c
unsigned char paethPredictor(short a, short b, short c) {
    short pa = LODEPNG_ABS(b - c);
    short pb = LODEPNG_ABS(a - c);
    short pc = LODEPNG_ABS(a + b - c - c);
    if(pb < pa) { a = b; pa = pb; }
    return (pc < pa) ? c : a;
}
```
The two comparisons (`pb < pa`, `pc < pa`) create **up to 4 paths per byte**. For a scanline of length L, filter type 4 creates up to **4^L paths just for one scanline**. Moreover, each `recon[i]` feeds into the computation of `recon[i + bytewidth]` as parameter `a`, so the symbolic expressions compound.

For an image with H scanlines, the `unfilter` function (lines 4136-4164) calls `unfilterScanline` for each row, where `prevline` from the previous row feeds into filter types 2, 3, and 4. The symbolic expressions from row N propagate into row N+1, causing expression trees to grow as **O(width x height)** in depth.

Combined with the symbolic filter type byte creating 5 branches per row, a 4x4 RGBA image (16 bytes per row, 4 rows) creates 5^4 = 625 filter-type combinations, each with O(4^16) Paeth branches per row in the worst case.

**KLEE Failure Mode**: Expression size explosion in the solver. The symbolic expressions for reconstructed pixel values become enormous nested trees of additions and conditional selections, causing solver queries to time out even for very small images.

---

## Summary Table

| Case Study | Root Cause | Key Lines | KLEE Failure Mode |
|---|---|---|---|
| 1. CRC32/Adler32 | Non-invertible hash constraints | 2318-2325, 2105-2108 | Solver cannot invert checksums |
| 2. Huffman decoding loop | Multiplicative branching per iteration | 1160-1243, 978-991 | Path explosion (O(6^N) per N iterations) |
| 3. Dynamic tree construction | 4-stage cascading symbolic constraints | 1009-1140 | Compound constraint infeasibility |
| 4. Multi-layer format constraints | Sequential constraint gates | 3958-3993, 2079-2100 | Only error paths explored |
| 5. LZ77 hash chain search | Triple-nested data-dependent loops | 1492-1639, 1544-1588 | O(n x chain x match) state explosion |
| 6. Scanline filter reconstruction | Sequential data dependencies + branching | 4006-4134, 3879-3886 | Expression tree exponential growth |
