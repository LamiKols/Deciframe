from werkzeug.security import generate_password_hash

# Generate password hash for 'admin123'
password = 'admin123'
hash_value = generate_password_hash(password)
print(f"Password hash for '{password}': {hash_value}")