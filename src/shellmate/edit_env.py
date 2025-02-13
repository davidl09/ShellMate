import os
import subprocess

def edit_env():
    # Check if .env.example exists
    cwd = os.path.dirname(__file__)
    template_file = os.path.join(cwd, '.env.example')
    env_file = os.path.join(cwd, '.env')
    
    if not os.path.exists(template_file) and not os.path.exists(env_file):
        print(f"Error: {template_file} or {env_file} does not exist.")
        return
    
    if os.path.exists(env_file):
        template_file = env_file

    # Read the content from the template file
    with open(template_file, 'r') as f:
        content = f.read()

    # Write the content to a temporary file for editing
    tmp_file = os.path.join(cwd, '.env.tmp')
    with open(tmp_file, 'w') as f:
        f.write(content)

    # Determine which editor to use (default to nano if EDITOR is not set)
    editor = os.environ.get('EDITOR', 'nano')

    # Open the temporary file in the editor
    subprocess.call([editor, tmp_file])

    # Once editing is done, read the edited content
    with open(tmp_file, 'r') as f:
        new_content = f.read()

    # Write the new content to the .env file
    with open(env_file, 'w') as f:
        f.write(new_content)

    # Clean up the temporary file
    os.remove(tmp_file)
    print(f"Writing to {env_file}")
    print("The .env file has been created/updated. Please restart the application")

# Example usage
if __name__ == '__main__':
    edit_env()
