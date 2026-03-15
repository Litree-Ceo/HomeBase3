# HomeBase3

## Setup

### 1. Configure API Keys

1. Copy the example environment file:

   ```
   copy .env.example .env
   ```

2. Edit `.env` and add your Anthropic API key:

   ```
   ANTHROPIC_API_KEY=your-actual-api-key-here
   ```

3. Get your API key from [Anthropic Console](https://console.anthropic.com/)

### 2. Using Claude Code

Once your `ANTHROPIC_API_KEY` environment variable is set, Claude Code will use your API key automatically.

To verify it's working, run:

```powershell
$env:ANTHROPIC_API_KEY
```

You should see your API key printed (or set it if empty).

## Security Notes

- Never commit `.env` files to version control
- The `.gitignore` file prevents this
- Only `.env.example` should be committed (contains placeholder values)
