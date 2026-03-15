# LiTreeLabStudio-Vs-1 - Avatar Assistant Workspace

This workspace is set up for your interactive Avatar Assistant, supporting a multi-style UI with Python and Node.js backend capabilities.

## Features
- **Avatar Interface**: Dynamically swap between Pixar, Cyberpunk, Steampunk, and Anime styles.
- **Moods & Actions**: Displays images/videos based on interactions (e.g. happy, thinking, surprised, talking).
- **Extensible Backend**: Includes `hello.py` and `hello.js` starters for adding AI models or logic later.

## Quick Start
1. **Launch**: Open `.vscode/tasks.json` and use the VS Code 'Run Task' menu to run `"Open assistant.html in browser"`.
2. **Customize**: Replace the placeholder image/video files in the project directory with your generated avatar assets (e.g., `avatar_pixar_happy.png`, `talking.mp4`).
3. **Backend Integration**: Build logic in Python or Node.js to trigger the avatar actions dynamically.

## Workspace Structure
- `assistant.html`, `avatar.html`: Web interface files
- `styles.css`, `main.js`: Interface styling and interactions
- `hello.py`, `hello.js`: Backend starter logic
- `.vscode/tasks.json`: VS Code build tasks for easy execution

## Next Steps
- Link the assistant UI to an AI backend for realistic conversational features.
- Expand the library of moods and reactions by saving new files that follow the naming convention (e.g., `avatar_<style>_<mood>.png`).