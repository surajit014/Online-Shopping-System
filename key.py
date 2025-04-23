import os

# Generate 24 random bytes (192 bits) and encode as hex
secret_key = os.urandom(24).hex()
print(secret_key)  # Example: '76eff09d4c770294ea1cb26bfed1f05ab3fabfbceb23ef67'