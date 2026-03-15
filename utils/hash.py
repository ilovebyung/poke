import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Pre-hashing all plain text passwords once
# stauth.Hasher.hash_passwords(config['credentials'])

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)


##############################################################
# Run to hash passwords once #################################
##############################################################


# Load the config
with open('config.yaml.bak') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Hash the passwords
stauth.Hasher.hash_passwords(config['credentials'])

# Write back to config.yaml
with open('config.yaml', 'w') as file:
    yaml.dump(config, file, default_flow_style=False)

