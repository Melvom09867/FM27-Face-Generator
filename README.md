# FM27 Face Generator

🇩🇪 *Deutsche Anleitung: [LIESMICH.md](LIESMICH.md)*

Creates **realistic player faces for Football Manager 27** in the right format
(**250 × 250 px, PNG**) – e.g. for your new youth intake. You then simply drag the images onto
the player in the game with the **FaceDrop** mod.

**Features at a glance**

- **Country of birth** (all 211 FIFA countries) and **ethnicity** – automatically matched to the country or set manually
- **Dual heritage**, e.g. "born in Germany, parents from Ghana" or "one parent from Morocco"
- **Age** (also as a range), **gender**, hair colour, hairstyle, facial hair, expression, clothing/colour, background
- **Import the player list from FM** – a matching image for every youth player, named after the player
- **Personality** from FM (e.g. Mercenary → neck tattoo & gold chain, Model Professional → well-groomed & focused)
- **Ageing set** – the same face at 16, 20, 25, 30 … years
- **Free choice of save location**, including automatic detection of your FM folder
- **FM cut-out style** like real facepacks: the head fills the image, background **cut out to transparent** by AI
- Gallery with "Re-roll", "Delete", "Show in folder"; log file `generiert.csv`
- **Reload previously created images** – e.g. to create an ageing set years later
- **20 languages** – every FM27 language (except Arabic); all translations except German are AI-generated

---

## Installation (step by step)

You need **Windows 10 or 11** and an **internet connection** (for the free online image AI).
You do **not** need to install Python or anything else.

### 1. Download the program

**Option A – Release (easiest):**
1. On this project's GitHub page, click **Releases** on the right.
2. Download **`FM27-FaceGenerator-win.zip`** from the latest release.

**Option B – from the automatic build:**
1. Be signed in to GitHub (downloads from "Actions" require an account).
2. Click the **Actions** tab at the top → choose **"Windows-EXE bauen"** on the left.
3. Open the latest run with a green tick ✅.
4. At the very bottom under **Artifacts**, click **FM27-FaceGenerator-windows** → a ZIP file is downloaded.

### 2. Extract

1. In your Downloads folder, **right-click the ZIP → "Extract All…"**.
2. Move the extracted folder to a permanent place, e.g. `C:\Tools\FM27 Face Generator`
   or simply your desktop. (Don't run it directly from inside the ZIP!)
3. The **"FM27 Face Generator"** folder contains: `FM27-FaceGenerator.exe`, the `_internal` subfolder (part of
   the program – don't delete or move it!), this `README.md` (English), the German guide `LIESMICH.md`, the patch
   notes and `laender.beispiel.json`. Always keep the **whole folder** together.

### 3. First start

1. **Double-click** `FM27-FaceGenerator.exe`. The generator opens in the foreground after a few seconds.
2. If **"Windows protected your PC"** (SmartScreen) appears:
   click **"More info"** → **"Run anyway"**. This happens because the program isn't commercially code-signed.
3. If your **antivirus** complains: some scanners react to self-extracting programs (PyInstaller).
   The EXE is built automatically and publicly traceable from this source code.
4. A small **language selection** window appears (default: German). Pick your language and click **OK**.
   Tick **"Don't ask again at startup"** to skip this window in future.
5. Optional: right-click the EXE → **"Send to" → "Desktop (create shortcut)"**.

### 4. Choose where to save

At the bottom of the window next to **"Save to:"**:

- **"Find FM folder"** – automatically finds `Documents\Sports Interactive\Football Manager …`
  (or your own FM user data folder if you moved it with the Steam launch option `user_data_location="…"`)
  and suggests `…\graphics\FM27 Face Generator` (choose "No" to pick a folder inside the FM directory yourself).
- **"Choose folder…"** – pick any folder.
- **"Open"** – opens the folder in Explorer.

The save location and all other settings are remembered automatically.

> **Tip:** Since you drag the images into the game with FaceDrop, the folder can be anywhere.
> A dedicated subfolder (e.g. `FM27 Faces`) keeps things tidy.

### Changing the language

Any time via the **"Language: …"** button at the bottom right. The interface switches immediately –
settings, gallery and a loaded player list are kept.

Available: Deutsch, English, Español (España), Español (Latinoamérica), Français, Italiano, Nederlands, Dansk, Norsk, Svenska, Polski, Português (Brasil), Português (Portugal), Русский, Türkçe, Ελληνικά, Bahasa Indonesia, 日本語, 한국어, 简体中文.

> **Note:** all translations except German were created with AI and are marked as such in the language
> selection (e.g. "English (AI-translated)"). Suggestions for improvements are welcome.
Countries, hair colours, personalities etc. are translated too. In languages other than German and English,
personalities also show the English FM name, e.g. "Mercenario (Mercenary)".

### Updates

When a new version is available, a notice appears at startup:

- **"Update now"** downloads the new version, replaces the program in its folder and restarts the generator – done.
  Your settings and own files such as `laender.json` are kept.
  (Only works if the program folder is writable, e.g. not inside `C:\Program Files`. Otherwise the button is
  missing and the download page remains.)
- **"Open download page"** opens the page in your browser.
- **"No, I want to play"** closes the window.

 With **"Don't show this version again"** exactly that version is no
longer announced – but the next newer one is. (Turn off: **Output** tab → "Check for updates at startup".
Only a request to GitHub is sent, no personal data.)

Manually: download the new version, extract it and copy the contents of the "FM27 Face Generator" folder over
the old program folder (or replace the old folder with the new one).

> **Once when moving from 1.8.7.1 or older to 1.8.7.2+:** from 1.8.7.2 the generator is a program folder
> (EXE + `_internal`) instead of a single EXE – it starts much faster. Please do this one switch **manually**:
> download the new ZIP, extract it, delete the old `FM27-FaceGenerator.exe` and use the new folder. After that
> "Update now" works automatically again.
What changed is listed in `PatchNotes.txt`.

**Test switch:** with **"Include test versions"** (**Output** tab, next to "Check for updates at startup") the
update notice also offers test versions (pre-releases). Normally leave it off.
Your settings are kept (stored in `%APPDATA%\FM27FaceGenerator`).

### Uninstall

Delete the program folder. Optionally also delete `%APPDATA%\FM27FaceGenerator` (settings and cut-out model).

---

## Usage

### Single images / a whole intake

1. **Player** tab: choose the **country of birth** (typing filters the list) and set the age (default 15–17).
2. Optionally set details in the **Look** tab, e.g. a shirt in your club colours.
3. Enter the **count** at the bottom and click **"Generate images"**.
4. Don't like an image? Click it in the gallery → **"Re-roll"** (replaces the file).
5. In the game, drag the matching PNG onto the player with FaceDrop – **straight from the gallery**
   (drag the thumbnail or the large preview into the FM window) or from the folder as before.

### The "Newly created" and "Gallery" tabs

- **Newly created**: the images from this session (and anything you add via "Load images…") – newest first.
- **Gallery**: **all images in your save folder** (including per-country subfolders), newest first. Use the
  **search box** to filter by file name – e.g. `Mercenary`, `Netherlands` or `16J`. From here you can drag, rename,
  delete and **start an ageing set directly** as well. "Refresh" re-reads the folder.

**File names**: the default is now `Country_AgeJ_Personality_ID`, e.g. `Netherlands_16J_Very-Ambitious_2106529392.png`
(without personality: `Netherlands_16J_2106529392.png`; with the German interface the German names are used).
If you create e.g. 4 images but only need one, you can recognise the others later by their name.
Adjustable in the **Output** tab → "File name".

### Gallery: drag, rename, delete

- **Drag**: hold the left mouse button and drag an image from the gallery into another program
  (FM with FaceDrop, Explorer …). Several selected images are dragged together.
  FM must run in **windowed mode**. If one program runs "as administrator" and the other doesn't,
  Windows blocks dragging – then start both the same way.
- **Select several**: **Ctrl + click** (add/remove) or **Shift + click** (range).
- **Rename**: **"Rename (F2)"** button or the **F2** key – e.g. to the player's name. Ageing sets still work
  afterwards (the info is stored inside the file).
- **Delete**: **"Delete"** button or the **Del** key – after confirmation the images go to the **Recycle Bin**
  (restorable).
- **Copy**: **"Copy (Ctrl+C)"** button or **Ctrl+C** – copies the image file like Explorer does.
  In FM hover over the portrait and press **Ctrl+V** (FaceDrop). Handy when dragging doesn't work (e.g. full screen).

### Working with FaceDrop

The generator detects FaceDrop automatically – even if your FM user data folder lives elsewhere via the Steam
launch option (`user_data_location="…"`). If there are several FaceDrop folders (e.g. the old location kept as a
backup after moving), it takes the one FaceDrop used last. Status and settings: **Output** tab → **FaceDrop**
("Choose folder …" if needed, "Detect automatically" resets it).

> **Important:** Nothing in FaceDrop's folders is **ever changed** – they are only read.

- **Gallery → Show: Save folder | FaceDrop**: with "FaceDrop" you see the images that are already **in the game** –
  per **career** (save game) or "Real players". The **player ID** is shown too. These images can be viewed,
  copied, dragged and used for an **ageing set** (the new images go to your save folder), but not renamed,
  deleted or re-rolled.
- **✓ in the game**: your own images that FaceDrop has already taken over get a green check mark in the
  generator's gallery (visible as long as you keep your copy – i.e. after "No" when cleaning up, or with "Off").
- **Clean up duplicate images**: when you drop an image onto a player with FaceDrop, FaceDrop copies it into its
  folder – so it exists twice on disk. The generator notices this (at startup and while running) and asks whether
  **your** copy should go to the Recycle Bin. FaceDrop's copy stays, nothing changes in the game. Setting:
  **Output → FaceDrop → Duplicate images**: *Ask* (default), *Clean up automatically* or *Off*.
  Only images created by the generator itself are touched.

### Dual heritage (parents from another country)

In the **Player** tab choose a second country under **"Parents' origin"** and set **"Parents"**:

| Setting | Result | Example |
|---|---|---|
| **Both parents from this country** | Looks like the parents' country | born in Germany, parents from Ghana |
| **One parent (mixed)** | Mixed heritage from both countries | French father, Moroccan mother |
| **Random** | one or the other per image | for a diverse intake |

The distribution is shown right below. "—" means no second origin.

### Importing the player list from Football Manager

This gives every youth player a matching face automatically – with their name as the file name.

**Export in Football Manager:**
1. Open the player list (e.g. youth team or youth intake preview).
2. Adjust the view so that at least the columns **Name**, **Nat** (nationality) and **Age** are visible.
   Optional: **2nd nationality**, **Personality** and **UID** (unique ID).
3. Select all players (**Ctrl + A**), then press **Ctrl + P** ("Print screen").
4. Choose **Web page** (`.html`) or **Text file** (`.txt`) and save.

**In the generator:**
1. Open the **"Player list (FM import)"** tab on the right → **"Load list…"** → choose the file.
2. Check: players with an **orange** country weren't recognised – select them and fix the country at the bottom ("set").
3. Choose the **file name**: `Name` (e.g. `Jonas Müller.png`), `UID` or `Name_UID`.
4. **"With 2nd nationality"** controls how players with two nationalities look (see table above).
5. **"Generate for all"** (or "For selection" / "Only without image"). The status shows ✓ and the file name.
   Double-click a player to open their image.

Age, country, 2nd nationality and personality come from the list; gender, look and background from the
settings on the left. Players without a personality in the list get the setting from the "Personality" section of the **Player** tab.
Below the list you can change country, 2nd country and personality for selected players afterwards.
Your own CSV file (e.g. from Excel) works too – header e.g. `Name;Nation;Age;2nd Nation;Personality;UID`.

**FM in another language?** Usually no problem: column names (e.g. *Nome/Età/Nazionalità*, *Nom/Âge*, *名前/年齢/国籍*),
country names (e.g. *Germania*, *Allemagne*, *ドイツ*, *독일*) and personalities are recognised in these languages –
as are the usual FIFA codes such as `GER`, `FRA`, `JPN`. For the languages added in 1.8.7.1 (Dutch, Danish,
Norwegian, Swedish, Polish, Russian, Turkish, Greek, Indonesian, Chinese) the column names are estimated and not yet
checked against real FM exports – if it doesn't work, switch FM to English for the export.

### Personality

In the **Player** tab under the heading **Personality** you choose one of the 40 FM personalities.
It sets the **facial expression** and adds matching **features**, for example:

| Personality | Typical features |
|---|---|
| Mercenary | neck tattoo, gold chain, diamond earrings, designer haircut, smug grin |
| Model Professional / Model Citizen | well-groomed, neat haircut, no jewellery, calm and focused or friendly |
| Perfectionist | perfectly styled, groomed eyebrows, intense gaze |
| Born Leader / Charismatic Leader | confident posture, assured look |
| Temperamental / Unsporting | furrowed brow, scar, dark look, maybe a tattoo |
| Casual / Slack | messy hair, tired look, wrinkled shirt |
| Jovial / Light-Hearted | big warm smile |
| Low Self-Belief | shy, uncertain expression |

- **Intensity**: Subtle (1 feature), Normal (2), Strong (3) – which features are used is randomised per image.
- **Tattoos from**: minimum age for tattoos (default 16). Younger players get e.g. an earring or chain instead.
- **Random**: every image gets a random personality.
- The features of each personality are shown in the tab as soon as you select it.

### Ageing set (the same face at different ages)

1. Select an image in the gallery.
2. Below the gallery, enter the ages under **"Ageing set"**, e.g. `16, 20, 25, 30, 34`
   (ranges like `25-28` work too).
3. Click **"Create"**. Files like `Jonas Müller_mit20.png`, `Jonas Müller_mit30.png` … are created.

Origin, hair, clothing, personality etc. stay the same; from the mid-20s more mature features are added,
from the early 30s fine lines and later grey temples.

**Ageing set for older images (later on):** click **"Load images…"** at the top right of the gallery and choose
previously created images (multi-select with Ctrl/Shift). Then select an image as above and click "Create".
The new images are saved in the same folder as the loaded image.

| Image | What happens |
|---|---|
| Created with **version 1.7 or later** | All info is stored invisibly inside the PNG – the ageing set hits exactly the same person. FM and FaceDrop are not affected. |
| Created with an **older version** | The info (seed, description) is taken from `generiert.csv` in the same folder – only the age is swapped. |
| **Other image** without info | Only possible with **local Stable Diffusion**: the image itself is used as a template, the description comes from the current settings. |

Tip: keep `generiert.csv` in the image folder – it's the "memory" for older images.

> **Honest note:** with the **online AI** the person looks *similar* at every age but isn't always exactly
> the same. With **local Stable Diffusion** the original image is used as a template (image-to-image) –
> the face is preserved much better.

---

## Which image AI is used?

The faces are created by an image AI; the program then crops them and scales them to 250 × 250 px.
Choose in the **AI** tab:

| Option | Pros | Cons |
|---|---|---|
| **Pollinations (online, free)** – default | No account, no graphics card needed, ready to go | Internet required, without a key only **1 image every 45 seconds** |
| **Local: Stable Diffusion WebUI** (AUTOMATIC1111 / Forge) | Offline, no limits, best quality with photorealistic models, better ageing sets | Own installation + NVIDIA graphics card (approx. 6–8 GB VRAM or more) |

**Pollinations without a key:** 1 image every 45 seconds is allowed. The program respects this automatically
and shows the waiting time at the bottom ("Free limit … 30 s left"). 20 images take about 15 minutes – just let it run.
The "pollinations.ai" watermark added at the bottom right without a key is cropped off automatically.

**Faster with a key:** get a key at *enter.pollinations.ai* (images then cost a small amount of credit)
and enter it under "API key" in the *AI* tab. This removes the waiting time and the watermark.

**Local:** see the next section.

---

## Setting up local Stable Diffusion (free, unlimited, best quality)

Runs entirely on your PC: no internet needed, no waiting, no watermark, no costs apart from electricity.
Ageing sets work much better (the face stays recognisably the same person).

**Requirements:** NVIDIA graphics card with at least 6 GB VRAM (8 GB+ recommended), approx. 25 GB of free disk space.
An RTX 3060 / 4060 or better is ideal – e.g. an **RTX 4080 Laptop GPU (12 GB)** creates an image in about 5–10 seconds.

> For large graphics cards, Windows sometimes shows a wrong "Adapter RAM" value (e.g. 1,048,576 bytes) –
> that's a known display bug and not a problem.

### Step 1 – Update the graphics driver
Install the latest driver via the **NVIDIA App** (or nvidia.com → Drivers). Restart afterwards.

### Step 2 – Download Stable Diffusion WebUI Forge
1. Open the GitHub page **"lllyasviel/stable-diffusion-webui-forge"**.
2. In the **"Installing Forge"** section (or under *Releases*), download **one** one-click package –
   recommended: **`webui_forge_cu121_torch231.7z`** (approx. 1.7 GB, Python included).
   You don't need the other variants.
   > **Download stuck at "1.7 GB of 1.7 GB" / "Unconfirmed … .crdownload"?**
   > The file is complete, Chrome is just waiting for your confirmation: press **Ctrl + J** in Chrome
   > and click **"Keep"** or **"Download anyway"**. You may also need to wait for the virus scan to finish.
   > Afterwards the file has its proper name `webui_forge_….7z`.
3. Extract it with **7-Zip** (free, 7-zip.org) – ideally into a short path **without spaces**,
   e.g. `C:\AI\Forge`. Not into "Program Files" or onto the desktop.

### Step 3 – One-time setup
1. In the Forge folder, double-click **`update.bat`** and wait until the window closes.
2. Double-click **`run.bat`**. The first start takes **10–20 minutes** (downloads packages and a default model).
   It's ready when the browser opens with the Forge interface, or the black window shows
   `Running on local URL: http://127.0.0.1:7860`.
3. Close Forge again (close the black window).

### Step 4 – Enable the interface for the generator
1. Open the **`webui`** subfolder inside the Forge folder.
2. **Right-click `webui-user.bat` → "Edit"** (opens Notepad).
3. Change the line `set COMMANDLINE_ARGS=` to:
   ```
   set COMMANDLINE_ARGS=--api
   ```
4. Save and close.

### Step 5 – Download a photorealistic model
The bundled default model produces rather artificial faces. Much better for real player photos is **RealVisXL**:
1. Search for **"RealVisXL V5.0"** on **civitai.com** (free account) or **huggingface.co**.
2. Download the file `RealVisXL_V5.0…safetensors` (approx. 6.5 GB).
3. Put it into the **`webui\models\Stable-diffusion`** folder in the Forge directory.

Alternatives with similarly good results: "Juggernaut XL", "epiCRealism XL".

**Normal or "Lightning"?** Both RealVisXL variants work. *Lightning* is about 5× faster
(only ~6 steps), the normal version slightly more detailed. The generator detects Lightning/Turbo models
automatically and then uses suitable values (6 steps, CFG 1.5, sampler DPM++ SDE Karras) –
you don't need to change anything.

### Step 6 – Start and connect
1. Start **`run.bat`** and wait until the Forge interface appears in the browser.
2. In Forge, on the **"Txt2img"** tab, set **"UI"** to **"xl"** in the bar at the very top and choose the
   **RealVisXL** model under **"Checkpoint"** (once – it's remembered).
   You don't need the "Checkpoint Merger", "Img2img", "Extras" etc. tabs.
3. In the FM27 Face Generator: **AI** tab → image AI **"Local: Stable Diffusion WebUI"**.
   Size 1024 px and "no pause" are set automatically.
4. Click **"Test connection"** – you should see "Connection OK" and the RealVisXL model.
5. Generate images as usual. Forge (the black window) must stay open.

**Recommended values** (preset): generation size 1024, 30 steps, CFG 5
(automatically 6 steps, CFG 1.5 for Lightning models).

| Problem | Solution |
|---|---|
| "No connection to http://127.0.0.1:7860" | Forge isn't running – start `run.bat` and wait until the interface appears |
| "The interface (API) is turned off" | Step 4: add `--api` to `webui\webui-user.bat`, restart Forge |
| Faces look artificial/painted | Select the RealVisXL model at the top of Forge (steps 5/6) |
| "Out of memory" error | Set the generation size to 768 or close other programs (games!) |
| Laptop: very slow | Plug in the laptop, set Windows power mode to "Best performance" |

Tip: running Football Manager and Forge at the same time works, but better generate images beforehand –
both need video memory.

### Start Forge automatically with the generator

**AI** tab → click **"…"** next to **"Forge folder"** and choose Forge's main folder (where `run.bat` and
`update.bat` are, e.g. `C:\AI\Forge`). Then tick **"Start and stop Forge with the generator"**.

- From the next start on, Forge boots **invisibly in the background** (the bottom shows "Forge is starting …",
  usually 30–90 seconds), without opening a browser window.
- When you **close the generator**, Forge is shut down too – but only if the generator started it.
  If Forge was already running, it stays on.
- **"Start now"** starts Forge immediately without restarting the generator.
- If something goes wrong, Forge's log is in `%APPDATA%\FM27FaceGenerator\forge.log`.

---

## Customising countries / distributions

The ethnicity distributions per country are rough approximations. To adjust or extend them:
rename `laender.beispiel.json` to **`laender.json`**, put it **next to the EXE** and edit it (e.g. with Notepad).
Country keys are the German country names used internally (e.g. `Deutschland`, `Färöer`).

```json
{
  "Färöer": { "en": "Faroe Islands", "mix": { "EUR_N": 100 } }
}
```

Ethnicity codes: `EUR_N` (Northern Europe), `EUR_W` (Western/Central Europe), `EUR_S` (Southern Europe),
`EUR_E` (Eastern Europe), `BALKAN`, `CAUCASUS`, `MIDEAST`, `AFR_N` (North Africa), `AFR_W` (West Africa),
`AFR_C` (Central/Southern Africa), `AFR_E` (East Africa), `AFRO_DIA` (Afro-Caribbean/African American),
`LAT` (Latin America), `INDIG` (indigenous), `ASIA_E`, `ASIA_SE`, `ASIA_S`, `ASIA_C`, `PACIFIC`, `MIXED`.

Countries the program doesn't know still work – the AI then decides from the country name alone.

---

## Keyboard use

- **Country and personality fields**: click into the field and type (e.g. `Ivo` or `merc`) – the filtered list opens with the best match highlighted (Ivory Coast). **↑/↓** moves within the list, **Enter** confirms, **Esc** closes.
- **All other drop-downs**: click and type – the list opens and jumps to the matching entry (e.g. `bl` → Blond/Black), **Enter** confirms.
- **Gallery**: **F2** = rename, **Del** = Recycle Bin, **Ctrl+C** = copy image (in FM: Ctrl+V), **Ctrl/Shift + click** = select several.

## Shirt in club colours

**Look** tab: choose **Clothing** (e.g. "Jersey without logo"), **Shirt colour**, **Pattern** (plain, vertical stripes,
horizontal hoops, contrasting sleeves, contrasting collar) and **Second colour**.
With **"Club preset → Save…"** the generator remembers the combination under a name (e.g. "My club") –
later just pick it from the list.

## Tips for realistic results

- The default is **"Transparent (FM cut-out)"** – cropping and cut-out are modelled on real FM facepack images
  (the head fills the image, hair reaches the top edge, neck and collar at the bottom).
- Adjust **Zoom** and **Face height** (Output tab) to match your other facepack images if needed
  (default: zoom 1.6 / face height 0.56).
- A **training top** in club colours (Look tab → Shirt colour) looks like a club media day photo.
- Keep **skin details** enabled – slight blemishes/freckles look less "AI-smooth".
- Add your own English keywords in the **Extra** field, e.g. `green eyes, small scar on chin`.

## Troubleshooting

| Problem | Solution |
|---|---|
| Long waiting time between images | Normal without a key (free limit 45 s). For more speed: enter an API key (AI tab) |
| "Pollinations rejected the request" (HTTP 401/403) | Check or enter the API key in the AI tab |
| Features (e.g. tattoo) missing from the image | Choose intensity "Strong" or "Re-roll" – the AI doesn't render every detail every time |
| "Local Stable Diffusion WebUI not reachable" | WebUI isn't running or was started without `--api`; check the address |
| Face not centred | Adjust zoom/face height in the Output tab or "Re-roll" |
| First image takes long ("One-time download of the cut-out model") | Normal: for the first transparent image the AI cut-out model (approx. 170 MB) is downloaded once and stored in `%APPDATA%\FM27FaceGenerator\models` |
| Background remnants at hair/edges | "Re-roll" or choose background "White"/"Light grey" (then without cut-out) |
| Players in the list are orange | Country not recognised → select them and use "set" for the country |
| List isn't recognised | Show at least the columns Name + Nat (or Age) in FM and export again |

## Building it yourself (for tinkerers)

Install Python 3.10+ and double-click `build.bat` → folder `dist\FM27-FaceGenerator\` (with the EXE).
To run without building an EXE: `pip install -r requirements.txt` and `python run.py`.

**Adding or improving translations:** all texts live in `fm27facegen/locales.py` (one line per text with the
first 8 languages side by side), further languages one file each in `fm27facegen/lang/`, country names in
`fm27facegen/country_names.py` and `country_names_extra.py`. A test checks that every text
exists in all languages with the same placeholders.

## Further ideas

- **Classic facepack format**: files as `r-<UID>.png` + an automatically generated `config.xml` (usable without FaceDrop).
- **More AI providers**: ComfyUI (local) or paid services with very high quality.
- **Style matching**: automatically adapt colour look/brightness to a reference image from your facepack.

## Notes

- The faces are AI-generated and don't show real people.
- When generating online, only the description of the face is sent to the service – no player names
  and no personal data.
