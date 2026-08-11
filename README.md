# Ritu

Six gardens from around the world, each showing its real current weather and light. Kyoto at midday, Isfahan at dawn, a Cotswolds garden gone dark at 3am: the page reflects what's actually happening in each place right now, not a loop.

[Live site →](https://tamkin-anwar.github.io/ritu/)

## What's here

- Six gardens: a Japanese zen garden (Kyoto), a Persian chahar bagh water channel (Isfahan), a Mughal Indian marble archway (Agra), an English cottage garden (the Cotswolds), a Talavera fountain (Puebla), and a Balinese candi bentar gate (Ubud)
- Live weather and sun position for each garden's real city, pulled from Open-Meteo with no API key required
- A day/dawn/dusk/night lighting model: the photo's brightness and saturation, the page's paper and ink colors, and a soft color-tint overlay all shift with the actual time of day and season at that location, not a canned animation
- Rain, snow, and fog layers that switch on when a garden's real weather calls for them, masked to the photo's own silhouette so they only fall where the object is
- A language switcher where every tab shows that city's real local clock, ticking, plus a small icon for its current conditions, so the six times reveal themselves before you even pick a garden
- A photo pipeline that finds each photo's real content bounds against its background, crops tight, and pads it back out for a soft radial mask to feather into
- A page background color measured from the actual rendered pixel, after the CSS filter and mask are applied, not guessed from the source file
- Full keyboard support: left and right arrows move between gardens

## Tech stack

- Plain HTML, CSS, and vanilla JavaScript, no framework or build step
- [Open-Meteo](https://open-meteo.com/) for live temperature, cloud cover, precipitation, and sunrise/sunset, fetched client-side with no key or backend
- Python and Pillow for the offline image prep pipeline
- Canvas 2D in the browser for the seam-closing measurement

## Running locally

```
python3 -m http.server 8743
```

Open `http://localhost:8743`. Weather requires network access; if the fetch fails or is offline, the page falls back to each garden's plain daytime look and the clocks keep running regardless, since they don't depend on the weather fetch.

To reprocess a source image:

```
python3 scripts/prepare_image.py <name> --anchor-x <0..1> --anchor-y <0..1>
```

`name` matches a file in `source-images/`, and `anchor-x`/`anchor-y` mark the visual center of the subject as a fraction of its content box, used to position the mask and vignette.

## Credits

Design language carried forward from Doorsong. Built by **Anwar Creative Studio**.
