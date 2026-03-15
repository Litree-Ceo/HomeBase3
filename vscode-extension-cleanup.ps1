# VS Code Extension Cleanup Script
# Run this in PowerShell to uninstall all non-essential extensions

# List of extensions to keep
$keep = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.pylint",
    "ms-python.black-formatter",
    "ms-toolsai.jupyter",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "humao.rest-client",
    "astro-build.astro-vscode",
    "github.copilot-chat",
    "eamodio.gitlens",
    "ms-azuretools.vscode-docker",
    "ms-azuretools.vscode-cosmosdb",
    "ms-azuretools.vscode-azurecontainerapps",
    "ms-vscode.git"
)

# Get all installed extensions
$all = code --list-extensions

# Uninstall all except those in $keep
foreach ($ext in $all) {
    if (-not ($keep -contains $ext)) {
        Write-Host "Uninstalling $ext..."
        code --uninstall-extension $ext
    } else {
        Write-Host "Keeping $ext"
    }
}

Write-Host "Cleanup complete!"
