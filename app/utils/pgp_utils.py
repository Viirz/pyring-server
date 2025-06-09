import gnupg
import os

gpg = gnupg.GPG(gnupghome='/var/www/app/.gnupg')
AGENT_PGP_DIR = '/var/www/app/.pgp'

def get_server_public_key():
    """Read server public key from file"""
    server_pub_path = os.path.join(AGENT_PGP_DIR, "server_pub.asc")
    if os.path.exists(server_pub_path):
        with open(server_pub_path, "r") as f:
            return f.read()
    raise Exception("Server public key not found")

def import_agent_pubkey(uuid):
    # First check if key is already imported
    pub_fingerprint = get_agent_fingerprint(uuid)
    if pub_fingerprint and gpg.list_keys(keys=[pub_fingerprint]):
        return  # Key already imported, skip
    
    # Import key if not found
    pub_path = os.path.join(AGENT_PGP_DIR, f"{uuid}_pub.asc")
    if os.path.exists(pub_path):
        with open(pub_path, "r") as f:
            gpg.import_keys(f.read())

def get_agent_fingerprint(uuid):
    """Get fingerprint from the agent's public key file"""
    pub_path = os.path.join(AGENT_PGP_DIR, f"{uuid}_pub.asc")
    if os.path.exists(pub_path):
        with open(pub_path, "r") as f:
            key_data = f.read()
            # Parse the key to get fingerprint (you could cache this)
            imported = gpg.import_keys(key_data)
            return imported.fingerprints[0] if imported.fingerprints else None
    return None

def verify_and_decrypt_status(encrypted_data, agent_uuid):
    import_agent_pubkey(agent_uuid)
    
    # Decrypt the message
    decrypted = gpg.decrypt(encrypted_data)
    if not decrypted.ok:
        raise Exception("Decryption failed")
    
    print(f"Decrypted message: {decrypted.data}", flush=True)
    
    # For signed and encrypted messages, the signature info is available in the decrypted object
    if decrypted.valid:
        print(f"Signature verification: {decrypted.valid}, fingerprint: {decrypted.fingerprint}", flush=True)
        verified_fingerprint = decrypted.fingerprint
    else:
        # Fallback: try to verify the decrypted data separately
        verified = gpg.verify(decrypted.data)
        print(f"Fallback verification result: {verified.valid}, fingerprint: {verified.fingerprint}", flush=True)
        verified_fingerprint = verified.fingerprint if verified.valid else None
    
    if not verified_fingerprint:
        raise Exception("Signature verification failed")
    
    # Check to ensure it's the expected agent
    expected_fingerprint = get_agent_fingerprint(agent_uuid)
    if verified_fingerprint != expected_fingerprint:
        raise Exception(f"Signature from wrong agent: expected {expected_fingerprint}, got {verified_fingerprint}")
    
    return decrypted.data.decode('utf-8')

def sign_and_encrypt_command(command_data, agent_uuid):
    import_agent_pubkey(agent_uuid)
    agent_fingerprint = get_agent_fingerprint(agent_uuid)
    
    if not agent_fingerprint:
        raise Exception(f"Agent fingerprint not found for UUID: {agent_uuid}")
    
    encrypted = gpg.encrypt(
        command_data,
        recipients=[agent_fingerprint],
        sign=True,
        always_trust=True
    )
    if not encrypted.ok:
        raise Exception(f"Encryption/signing failed: {encrypted.stderr}")
    return str(encrypted)

def delete_agent_pgp_keys(agent_uuid):
    """Delete agent's PGP keys from keyring and file system"""
    try:
        # Get the agent's fingerprint before deleting files
        agent_fingerprint = get_agent_fingerprint(agent_uuid)
        
        # Delete the public key file
        pub_path = os.path.join(AGENT_PGP_DIR, f"{agent_uuid}_pub.asc")
        if os.path.exists(pub_path):
            os.remove(pub_path)
        
        # Delete the key from GPG keyring if it exists
        if agent_fingerprint:
            try:
                # Delete the key from keyring
                gpg.delete_keys(agent_fingerprint)
            except Exception as e:
                print(f"Warning: Could not delete key from keyring: {e}")
                
    except Exception as e:
        raise Exception(f"Failed to delete PGP keys: {e}")