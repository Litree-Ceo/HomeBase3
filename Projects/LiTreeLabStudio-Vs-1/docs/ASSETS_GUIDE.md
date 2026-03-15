# 🎨 Avatar Assets Guide

This guide explains how to add your own avatar images and videos to bring your assistant to life!

## 📁 Folder Structure

```
assets/
├── avatars/      # Avatar images for different styles and moods
├── videos/       # Video clips for talking animations
└── audio/        # Custom audio files (optional)
```

## 🖼️ Avatar Images

### Naming Convention

Place PNG images in `assets/avatars/` with this naming pattern:

```
avatar_{style}_{mood}.png
```

### Required Files

For each style, you need 4 mood images:

| Style | Happy | Thinking | Surprised | Talking |
|-------|-------|----------|-----------|---------|
| **Pixar** | `avatar_pixar_happy.png` | `avatar_pixar_thinking.png` | `avatar_pixar_surprised.png` | `avatar_pixar_talking.png` |
| **Cyberpunk** | `avatar_cyberpunk_happy.png` | `avatar_cyberpunk_thinking.png` | `avatar_cyberpunk_surprised.png` | `avatar_cyberpunk_talking.png` |
| **Steampunk** | `avatar_steampunk_happy.png` | `avatar_steampunk_thinking.png` | `avatar_steampunk_surprised.png` | `avatar_steampunk_talking.png` |
| **Anime** | `avatar_anime_happy.png` | `avatar_anime_thinking.png` | `avatar_anime_surprised.png` | `avatar_anime_talking.png` |

### Image Specifications

- **Format**: PNG (with transparency preferred)
- **Size**: 512x512 pixels minimum (square aspect ratio)
- **Style**: Circular avatar (will be clipped to circle in UI)
- **Background**: Transparent or matching the theme color

### AI Image Generation Prompts

Use these prompts with AI image generators (DALL-E, Midjourney, Stable Diffusion):

#### Pixar Style
```
A cute friendly robot character, Pixar 3D animation style, big expressive eyes, 
rounded features, soft lighting, solid color background, happy expression, 
high quality render --ar 1:1
```

#### Cyberpunk Style
```
A sleek robot with neon accents, cyberpunk aesthetic, glowing elements, 
dark background with neon lights, futuristic design, high tech appearance, 
digital art style --ar 1:1
```

#### Steampunk Style
```
A Victorian-era robot with brass gears and copper details, steampunk style, 
goggles, mechanical parts, warm sepia tones, antique aesthetic, detailed --ar 1:1
```

#### Anime Style
```
A cute robot character, anime manga style, big sparkly eyes, clean lines, 
vibrant colors, expressive pose, solid background, cel shaded --ar 1:1
```

## 🎬 Video Files

### Talking Animation Video

Place video files in `assets/videos/`:

```
talking.mp4
```

Or style-specific versions:
```
talking_pixar.mp4
talking_cyberpunk.mp4
talking_steampunk.mp4
talking_anime.mp4
```

### Video Specifications

- **Format**: MP4 (H.264 codec for best compatibility)
- **Duration**: 5-10 seconds (loops seamlessly)
- **Resolution**: 512x512 or 1024x1024
- **Aspect Ratio**: 1:1 (square)
- **Audio**: Optional (voice can be synthesized)

### Creating Talking Videos

**Option 1: AI Video Generators**
- Use Runway ML, Pika Labs, or similar
- Upload your static avatar image
- Animate the mouth/lip-sync

**Option 2: Animation Software**
- Adobe After Effects
- Blender (free)
- Live2D Cubism (for anime style)

**Option 3: Simple Loop**
- Subtle breathing animation
- Gentle head bob
- Blinking eyes

## 🔊 Audio Files (Optional)

Place custom audio in `assets/audio/`:

- `greeting.mp3` - Welcome sound
- `notification.mp3` - Message alert
- `thinking.mp3` - Thinking/processing sound

## 🛠️ Quick Start

Don't have images yet? No problem!

1. **Use Emojis**: The app shows cute emojis as placeholders
2. **Generate with AI**: Use the prompts above with any AI image tool
3. **Start Simple**: Just create one `avatar_pixar_happy.png` to begin

## 🎨 Customization Tips

1. **Consistent Character**: Use the same base character across all styles
2. **Mood Variations**: Change only facial expression between moods
3. **Style Consistency**: Keep the same pose/angle for all styles
4. **Test in App**: Preview immediately after adding files

## 📝 Example File List

Minimum setup (uses emojis for missing images):
```
assets/
└── avatars/
    └── avatar_pixar_happy.png
```

Full setup:
```
assets/
├── avatars/
│   ├── avatar_pixar_happy.png
│   ├── avatar_pixar_thinking.png
│   ├── avatar_pixar_surprised.png
│   ├── avatar_pixar_talking.png
│   ├── avatar_cyberpunk_happy.png
│   ├── avatar_cyberpunk_thinking.png
│   ├── avatar_cyberpunk_surprised.png
│   ├── avatar_cyberpunk_talking.png
│   ├── avatar_steampunk_happy.png
│   ├── avatar_steampunk_thinking.png
│   ├── avatar_steampunk_surprised.png
│   ├── avatar_steampunk_talking.png
│   ├── avatar_anime_happy.png
│   ├── avatar_anime_thinking.png
│   ├── avatar_anime_surprised.png
│   └── avatar_anime_talking.png
└── videos/
    └── talking.mp4
```

---

💡 **Pro Tip**: Start with just one style and expand later. The emoji placeholders work great while you're building your avatar collection!
