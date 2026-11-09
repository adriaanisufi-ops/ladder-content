# Lessons (keep adding, newest at the top)

## DEFAULT FORMAT from 2026-11-09 (Adriaan, binding, replaces the 18 to 20 s loops)
Every video is made like 2026-11-08-extra-1 ("You're not unmotivated. / You're vague."; spec in out/ is not in git, so the values are here):
- Spec values: "beat": 0.75 (80 BPM), "minlen": 4, "size": 64, "hook_size": 76, "x": 80, "y0": 720, "blob" about 0.45 (up to 0.8 on busy footage), black and white ("pre" starts with "hue=s=0,"). NEVER the "label" field (no series label like "HARD TRUTH #1" on screen) and never "cta".
- Length about 13.5 s: 4 blocks; blocks 1, 2 and 4 have 2 lines, block 3 may have 3. The last block flows back into the hook so the loop is seamless.
- Hook: the very first line, on screen from frame 1, max about 24 characters, a short "you/your" claim people want to react to ("You're not unmotivated."), with a 2 or 3 word gold answer ("You're vague.").
- Line width at size 64: keep every line at most about 26 characters (measure with PIL and Inter: x + width must stay under 940 px, hook under 1000 px). Split long sentences over two lines.
- Footage: clips tagged "driving" first (POV drives, dark roads, tunnels, mirrors: motion from the first frame, calm and dark), least recently used first. Fall back to dark calm car clips when no driving clip is free.
- Caption: first line uses search words (discipline, motivation, goals, self improvement), then "Send this to someone who ...", then "Comment BOOK and I'll send it to you.", then 4 hashtags. Also give one short question per video for Adriaan to post and pin as the first comment.
- Sound: tell him to pick a sound around 80 BPM so the text lands on the beat.
- More engagement (Adriaan 2026-11-09 wants more): put one concrete, recognisable list in the video ("The gym. The book. The call.") so people comment which one is theirs, and make the pinned comment a choice question about that list. No CTA on screen.
- Still compare watch time and full watch rate with the old 18 s loops when Adriaan sends numbers.

## Text position: middle of the screen (Adriaan, 2026-11-08, binding)
- On the phone, text at the top (y0 around 230 to 330) gets hidden behind TikTok's top bar, and text at the bottom (y0 1160) sits under the caption and buttons. Every line must be readable in the TikTok app.
- Default now: y0 = 740 for every video (text block roughly y 740 to 950 on the 1920 frame). All clips in clips.json are set to 740. Never go above y0 650 or below y0 850.
- TikTok safe zone to check against (1080x1920): keep text out of the top 200 px, the bottom 480 px (from y 1440) and the right rail (x above 940, y 880 to 1640). Keep lines at or under about 34 characters so they don't reach the right rail.
- When checking frames, draw these zones on the frames (ffmpeg drawbox) and confirm no text touches them. If the middle of the clip is busy with headlights, raise blob (up to 0.8) and add "eq=gamma=0.75:brightness=-0.05," to pre instead of moving the text up or down.

## Winners so far (Adriaan, 2026-11-07)
- Third pattern element: hard truth that takes away an excuse or a hope of rescue ("Nobody is coming...") gets saved most.
- "You didn't choose that thought." (3 Nov, pex-19452742, aerial highway, text top): 82 likes, 4 saves after 3 days. Caption: "Half the thoughts you obey today aren't even yours."
- "Your plan is built for who you wish you were." (29 Oct, ladder-src-14, dark tunnel drive, text bottom): also did well.
- "Nobody is coming to rebuild you." (4 Nov, pex-40074031, near black aerial street, text bottom): 54 likes, 9 saves, best save rate so far. Sound: "Mamnoun" by Ehab (slow, emotional). Caption: "Your past explains you. It doesn't excuse you."
- Shared pattern: a short "you/your" accusation about the person's own mind or self image (2 lines, punch of 3 to 5 words), the hook complete within 2 seconds, very dark calm footage with lots of empty space around the text.
- Do more of this: hooks that tell the viewer something about themselves they didn't notice ("You didn't choose...", "Your X is built for...", "That's not yours."). Remake these two with new footage and a follow up angle.
- Adriaan 2026-11-07: focus more on this winning style. Default now: hard truth "you" hooks, near black footage in black and white ("pre": "hue=s=0,..." before the grade).
- Sound is added by hand in TikTok: "Mamnoun" (Ehab) worked on a winner; slow, calm, emotional (piano, ambient, slow guitar), ideally around 60 or 120 BPM so the text lands on the beat.

## Text style Adriaan likes (2026-10-27)
- Liked: "Feeling motivated today? / Do less." Disliked the abstract ones ("bait and switch", "you're the sky", "preloading the state", "a tag you never read").
- So: talk straight to "you", a question or a command, short plain words, punch lines of 2 to 5 words, advice that goes against what people expect. Concrete images (bubbles pop), no literary metaphors that need a second read.

## Phase 1: followers first (Adriaan, 2026-10-27, replaces the CTA test)
- Goal now is followers and rewatches, conversion comes later. NO action on screen: no "Comment BOOK", no "link in bio", no "cta" field.
- Default is a pure seamless loop: the last block restates the point so it flows straight back into the first line. Length, pace and text size: see DEFAULT FORMAT at the top (about 13.5 s since 2026-11-09).
- The 3D book outro only now and then: one book video every other day at most, the rest loops.
- The hook is on screen from the first frame and is a claim or a pain, never the book or Adriaan's name.
- Caption can still end with "Comment BOOK and I'll send it to you." (it is not in the video).
- The CTA test (closings A/B/C, 27 Oct) is stopped. reel.py keeps the optional "cta" field for later.

## Our own results (as of 2026-10-23)
- Videos with cars at night perform best for us (01 highway, 02 city traffic, 11 night drive).
- Text that falls well: a first line that contradicts what people think ("Time doesn't actually speed up.", "Stop telling people your goals.").
- People, objects (match, incense) and abstract smoke footage did not land. Use vibe footage only.
- The only BOOK comment so far came from a video with the 3D book outro. Keep the outro on about 1 in 4 videos.
- A text that was a plain statement ("You tell someone you're fine...") was rejected. Pain or contrarian hooks win.

## From analysed videos
### theflintmind, 2026-10-21 (1,469 likes, 21 comments, 53s)
- Structure: warning hook aimed at "you", then 3 concrete situations, then the cost, then a reframe, then a quotable last line. The last line is also the first line of the caption, followed by a keyword CTA ("Comment Guide").
- Continuous voiceover over music; subtitles follow the spoken sentences.
- A new visual every 4 to 5 seconds with soft dissolves, about 12 visuals in total.
- Black and white abstract wireframes in a 16:9 band inside the 9:16 frame, one centered line of text below.

### Instagram ranking signals (Hootsuite, 2026)
- Watch time and completion, rewatches, sends per reach, likes per reach, follows after viewing.
- Ask for the send in the caption: "Send this to someone who ...".
- Trial Reels show a Reel to non-followers only: use them to test two hooks.
