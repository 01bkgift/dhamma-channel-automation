#!/usr/bin/env python3
"""
Generate B-roll images using OpenAI DALL-E API

Usage:
    python scripts/generate_broll_dalle.py \
        --prompt "Peaceful Thai Buddhist temple at sunrise" \
        --output "broll/temple/temple_sunrise.png" \
        --size "1792x1024"
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI library not found")
    print("💡 Install with: pip install openai")
    sys.exit(1)


def generate_broll_image(
    prompt: str,
    output_path: Path,
    size: str = "1792x1024",
    quality: str = "hd",
    style: str = "natural",
) -> bool:
    """Generate a B-roll image using DALL-E 3."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False

    client = OpenAI(api_key=api_key)

    print(f"🎨 Generating image: {prompt[:50]}...")

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
        )

        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt

        print(f"📝 Revised prompt: {revised_prompt[:100]}...")

        # Download image
        import urllib.request

        output_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(image_url, output_path)

        print(f"✅ Saved to: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to generate image: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate B-roll images with DALL-E")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument(
        "--size",
        default="1792x1024",
        choices=["1024x1024", "1792x1024", "1024x1792"],
        help="Image size",
    )
    parser.add_argument(
        "--quality", default="hd", choices=["standard", "hd"], help="Image quality"
    )
    parser.add_argument(
        "--style",
        default="natural",
        choices=["natural", "vivid"],
        help="Image style",
    )
    args = parser.parse_args()

    success = generate_broll_image(
        prompt=args.prompt,
        output_path=Path(args.output),
        size=args.size,
        quality=args.quality,
        style=args.style,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
