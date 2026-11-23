# Mobile Testing & HTTPS Camera Guide (MOBILE_TESTING_GUIDE.md)

Modern mobile operating systems (iOS Safari and Android Chrome) strictly enforce **Secure Context (HTTPS)** for `navigator.mediaDevices.getUserMedia`. Standard plain HTTP over local LAN IP addresses (e.g., `http://192.168.1.X:3000`) will block camera video streams with a security exception.

To test the **Live Camera Room Scanner** on a physical smartphone, choose one of the three verified methods below:

---

## Option 1: Free Cloudflare Tunnel (Zero Install on Phone — Recommended)

This gives you a secure `https://xxx.trycloudflare.com` URL in 5 seconds without router port forwarding.

1. In PowerShell/Terminal on your development machine, run:
```bash
npx cloudflared tunnel --url http://localhost:3000
```
2. Cloudflare will print a temporary secure URL:
```text
https://random-words-subdomain.trycloudflare.com
```
3. Open this HTTPS link on your phone in Chrome or Safari.
4. When prompted, tap **"Allow Camera"**.
5. Point your camera at any room wall to experience real-time temporal wall recolouring!

---

## Option 2: Local mkcert SSL Certificates

If you prefer testing directly over your local WiFi network:

1. Install `mkcert` on your host:
```bash
# Windows (via Chocolatey or Scoop)
choco install mkcert
mkcert -install
mkcert localhost 127.0.0.1 ::1 192.168.1.X
```
2. Run Next.js with the generated SSL certificates:
```bash
npm run dev -- --experimental-https --experimental-https-key ./localhost-key.pem --experimental-https-cert ./localhost.pem
```
3. Install the root CA certificate onto your phone and visit `https://192.168.1.X:3000`.

---

## Option 3: Android Chrome Remote Debugging over USB

If you have an Android device connected via USB with Developer Mode:
1. Open Google Chrome on your computer and navigate to:
```text
chrome://inspect/#devices
```
2. Under **Port Forwarding**, map port `3000` to `localhost:3000`.
3. On your Android phone, open Chrome and navigate to:
```text
http://localhost:3000
```
Chrome treats `localhost` as an intrinsically secure context, allowing full camera access without SSL warnings!

---

## Live Scanner Features on Mobile
- **Default Rear Camera**: Uses `facingMode: { ideal: "environment" }` by default for scanning walls.
- **Camera Switch**: Tap the toggle icon in the top right to switch between front and rear cameras.
- **Temporal Stabilization**: Optical EMA smoothing ($\alpha = 0.85$) prevents paint flickering across moving objects.
- **Still Capture**: Tap **"Capture & Analyse in Studio"** to transfer the still directly to high-resolution studio processing.
- **Low Light Warning**: If ambient room illumination drops below threshold, an alert advises turning on room lighting.
