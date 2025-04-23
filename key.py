import os

# Generate 24 random bytes (192 bits) and encode as hex
secret_key = os.urandom(24).hex()
print(secret_key)  
