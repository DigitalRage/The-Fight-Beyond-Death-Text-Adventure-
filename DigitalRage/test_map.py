#!/usr/bin/env python3
"""Quick test of map integration."""
from maps import map1

print(f"Map loaded: {len(map1)} rows")
print(f"First row length: {len(map1[0])}")
print("\nFirst 5 rows of map:")
for i, row in enumerate(map1[:5]):
    print(f"Row {i}: {row[:50]}...")  # Show first 50 chars

print("\n✓ Map integration successful!")
print(f"✓ map1 has {len(map1)} rows")
print(f"✓ Each row has ~{len(map1[0])} characters")
