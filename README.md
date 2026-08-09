# Susurrus

Six garden scenes from around the world, each staged as an isolated photograph and blended into the page so the crop, the color, and the shadow read as one continuous object instead of a pasted-in image.

[Live site →](https://tamkin-anwar.github.io/susurrus/)

## What's here

- Six gardens: a Japanese zen garden, a Persian chahar bagh water channel, a Mughal Indian marble archway, an English cottage garden, a Talavera fountain from Mexico, and a Balinese candi bentar gate
- A photo pipeline that finds each photo's real content bounds against its background, crops tight, and pads it back out for a soft radial mask to feather into
- A page background color measured from the actual rendered pixel, after the CSS filter and mask are applied, not guessed from the source file
- A seam-closing step that scans the rendered photo for where its content actually ends and clips the padding away, so the photo sits flush against the field beneath it with no visible gap
- A language switcher with a matching ink and paper palette per scene, including a dark palette for the Bali scene
- Full keyboard support: left and right arrows move between gardens
- An ambient sound bed synthesized live per garden with the Web Audio API: filtered noise tuned to the scene's material (sand, water, leaves), with occasional drips where a garden has a fountain or pond
- Moving over a garden gently raises the sound, the way a breath of wind would

## Tech stack

- Plain HTML, CSS, and vanilla JavaScript, no framework or build step
- Python and Pillow for the offline image prep pipeline
- Canvas 2D in the browser for the seam-closing and background color measurement
- Web Audio API for the synthesized ambient sound, no audio files

## Running locally

```
python3 -m http.server 8743
```

Open `http://localhost:8743`.

To reprocess a source image:

```
python3 scripts/prepare_image.py <name> --anchor-x <0..1> --anchor-y <0..1>
```

`name` matches a file in `source-images/`, and `anchor-x`/`anchor-y` mark the visual center of the subject as a fraction of its content box, used to position the mask and vignette.

## Credits

Design language carried forward from Doorsong. Built by **Anwar Creative Studio**.
