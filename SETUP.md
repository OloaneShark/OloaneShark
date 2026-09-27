# Setup

## Image Assets

Place your hero GIF here:

```text
assets/hero.gif
```

Place the Hotline Miami phone PNG here:

```text
assets/phone.png
```

Place cassette achievement PNG images here:

```text
assets/cassettes/source/
```

The generated cassette files are:

```text
assets/cassettes/current-blacklight.png
assets/cassettes/current-middleman.png
assets/cassettes/current-spotify.png
```

The `assets/cassettes/source/` files are preserved. The generated `current-*` files are replaced by the rotation script and GitHub Action.

## Rotate Cassettes

Run manually:

```bash
python scripts/rotate_cassettes.py
```

To run it from GitHub, open the repository Actions tab, select `Rotate cassette artwork`, choose `Run workflow`, and run it on `main`.

The workflow also runs every six hours. It commits only the generated cassette files when those files actually change.

## Spotify Developer App

1. Go to the Spotify Developer Dashboard.
2. Create an app.
3. Add this redirect URI:

```text
http://127.0.0.1:8888/callback
```

4. Save the app.
5. Copy the client ID and client secret.

Required scopes:

```text
user-read-currently-playing
user-read-playback-state
```

## Get A Refresh Token

Set these environment variables locally:

```bash
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
```

On Windows PowerShell:

```powershell
$env:SPOTIFY_CLIENT_ID="your-client-id"
$env:SPOTIFY_CLIENT_SECRET="your-client-secret"
```

Run:

```bash
python scripts/get_spotify_refresh_token.py
```

The script prints a Spotify authorization URL, waits for the local callback, exchanges the returned code, and prints `SPOTIFY_REFRESH_TOKEN`. It does not write secrets to the repository.

If the local callback cannot be used, run:

```bash
python scripts/get_spotify_refresh_token.py --manual
```

Then paste the returned authorization code when prompted.

## Vercel Environment Variables

Add these to your Vercel project:

```text
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
SPOTIFY_REFRESH_TOKEN
```

Do not commit `.env` or `.env.local`.

## Deploy To Vercel

1. Import this repository into Vercel.
2. Use the default project settings.
3. Add the Spotify environment variables.
4. Deploy.
5. Copy your Vercel domain.

In `README.md`, replace:

```text
YOUR-VERCEL-DOMAIN
```

with your actual Vercel domain.

## Hero GIF Size

The hero image is controlled in `README.md`:

```html
<img src="./assets/hero.gif" width="100%">
```

Changing `100%` to `90%`, `800`, `700`, or another width changes the displayed width. GitHub preserves GIF aspect ratio automatically when only width is specified.

## GitHub README Limits

GitHub profile READMEs cannot execute custom JavaScript or custom CSS. The answering-machine menu is static inside `README.md`; true hover or level-select behavior would need an external webpage.
