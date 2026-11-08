# Lessons (keep adding, newest at the top)

## Test format "Hard truth" (2026-11-08, waiting for results)
- First test video 2026-11-08-hardtruth-1: 13.5 s instead of 18 to 20, beat 0.75 (80 BPM), hook line bigger (hook_size 76), text size 64, small series label "HARD TRUTH #1" above the text, driving clip with motion from the first frame, comment bait in the hook instead of a CTA, pinned comment with a question.
- New reel.py spec fields: "beat", "hook_size", "label" (plus "size" and "x"). Number the label on from #1 when this format is used again.
- Compare its average watch time and full watch rate with the 18 s loops before making it the default.

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
- Default is a pure seamless loop in the style of ladder-reel-02 ("Time doesn't actually speed up."): 4 or 5 blocks, about 18 to 20 s, the last block restates the point so it flows straight back into the first line.
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
