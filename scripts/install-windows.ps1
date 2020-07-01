# powershell
# Feel free to suggest improvements, my powershell is quite "meh".

$INSTALL_DIR=".figgy/installations/first"

cd ~

# Create install directory
mkdir $INSTALL_DIR
cd $INSTALL_DIR

# Download Figgy
echo "Downloading figgy archive..."
Invoke-WebRequest -Uri https://www.figgy.dev/releases/cli/latest/windows/figgy.zip -OutFile figgy.zip

# Unzip
echo "Unzipping figgy archive..."
Expand-Archive .\figgy.zip

# Add DIR to path
cd figgy/figgy/figgy
$DIR=pwd

# Create symlink for figgy.exe
New-Item -ItemType SymbolicLink -Path "figgy" -Target "figgy.exe"

## Add Dir to path
echo "Adding installation directory [$DIR] to path."
$ENV:PATH="$ENV:PATH;$DIR"

# Permanently add to path for future sessions
setx /M PATH "$($env:path);$DIR"

echo "Cleaning up zip"
rm ../../figgy.zip

echo "Testing..."
figgy --version