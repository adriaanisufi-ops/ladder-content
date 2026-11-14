# Lessons (keep adding, newest at the top)

## DEFAULT FORMAT from 2026-11-13: VYZEE explainers (Adriaan: "this is good, make this kind of stuff always")
Approved video: "Price Tags" (spec: toolkit/specs/example-vyzee-price-tags.json). Replaces the ladder dialog below.
- Look: minimal glowing white line animation on black (little figure, shop window, tags, receipts, stairs, big glowing words, white pills), ONE gold moment at the end. Style reference: Adriaan's "Or we could go up" video.
- Sound: an AI voice (Kokoro am_michael, speed 1.05) is ALWAYS there. NO music in the file: Adriaan adds VYZEE (SOPHIE) in TikTok with "Use this sound" from his reference video, starting at 0:00. Deliver ONE file per video (voice only), never a second version with music.
- Everything is timed to the VYZEE beat grid in toolkit/vyzee.py: calm intro 0 to 16.4 s (hook + build + a question), silence at 16.4 s, DROP at 17.18 s (beat 31: the payoff starts exactly there, one hit per beat), loud part until 36.8 s, quiet part after 36.8 s for the emotional line and the gold finale. Length about 40 to 45 s.
- Render: python3 toolkit/vyzee.py SPEC.json out/<day>/<day>-<n>.mp4 (downloads the Kokoro voice the first time). Shot types: window, slam, versus, steps, bubble, week, streak, bigbar, check, tag_finale, ladder_finale, figure, gaps, alarm, void, chart, numbered, convert, edges (cloud to box), nail (belief driven in by strikes), scale (ledger), house (thoughts as visitors); text items: big, pill, small. Read the docstring and the example spec.
- MAKE IT USEFUL (Adriaan 2026-11-13: "lots of people are doing the same, make it actually useful"). Mood lines and pure metaphors are everywhere. Every video teaches ONE concrete method from the book that people can use tonight and will save: give it a name ("The Bad Day Rule"), show the problem in the intro, the numbered steps on the drop (one per beat, shot "numbered"), concrete examples (shot "convert": GYM -> 10 PUSHUPS), proof (shot "chart"), then the emotional line and a gold rule. Approved example: toolkit/specs/example-vyzee-bad-day-rule.json. Methods in the book: the bad day floor, two strikes (say your sentence after waking and before sleep), one do and one don't per day, give your goal edges (number, date, reason; stop announcing it; one goal above the rest for a season), catch the gap (name it, fix the next action, no speech), one action that's yours today without checking the outcome, sit in one gap a day with nothing in your hands.
- Be creative: every video is ONE visual metaphor from one chapter (Price Tags = a shop window of dreams whose tags hide the real price). Other ideas Adriaan saw: elevator vs stairs (Ladder Not Bubble, Don't Break the Streak), phone vs ladder (The Art of Boredom). Invent new ones per chapter; never reuse a metaphor that is in log.csv.
- Hook in the first second, on screen and spoken: provocative and personal ("You can't afford your dreams." / "And it's not about money."). End the intro on a question right before the silence ("Want to see what it really costs?") so the drop answers it.
- Words: stay close to Adriaan's own sentences from book.txt; short spoken lines; never any dash character.
- When Adriaan is in the chat, pitch the concept and ask him before building (he asked for that on 2026-11-13). In the unattended daily run, pick the concepts yourself and say in the message what each one is.
- Caption: the book only (see the dialog section below), plus a pinned comment question per video.

## Ladder dialog from 2026-11-12 evening (REPLACED on 2026-11-13 by the VYZEE explainers above) (Adriaan: "dit is perfect, maak vanaf nu 4 video's per dag op deze manier")
Approved video: "Juist" = the dialog about The Gap (label "Expectation outrunning action"), re-rendered with the text inside the phone frame. Replaces the ladder text format below.
- Render: python3 toolkit/ladder_dialog.py SPEC.json out/<day>-<n>.mp4 (spec example: toolkit/specs/example-dialog.json). No footage, no clips.json: the scene is drawn (silhouette, ladder, rain, gold).
- Script shape: 6 lines, alternating "you" and "ladder", ending on the ladder. "you" opens with a relatable confession or question (on screen from frame 1), then a short follow up ("What gap?", "What do you mean?"), then "So how do I ...?". The ladder answers short, then explains, then gives the turn: a concrete action in short sentences (held about 9 s, that is the rewatch moment).
- A label (the "title") names the idea in 2 to 4 words, like a psychology term ("Expectation outrunning action", "Rehearsal suffering", "Cheap dopamine", "Outcome gripping", "Performing to be chosen"). People save and share a name for what they feel.
- Line length: "you" lines max about 12 words, ladder lines max about 18 words (the renderer warns when a line gets too many rows). Questions are short.
- NO voice over (Adriaan 2026-11-12: he likes it without). Audio is only soft rain; he adds music in TikTok (he likes VYZEE by SOPHIE, drop on the start of the last answer). Always tell him the second the last answer starts.
- Text must stay inside x 130 to 950: tall phones crop about 100 px off each side of a 9:16 video. The renderer's layout does this; still check frames.
- Caption (Adriaan's choice): only the book.
  From my book: Burning Desire, True Belief, Fierce Plan, Relentless Action.
  (blank line) Comment BOOK and I'll send it to you.
  (blank line) 3 hashtags, e.g. #selfimprovement #discipline #mindset
  Plus one pinned comment question per video.
- WRITE DEEPER (Adriaan 2026-11-13: "het kan kwa tekst beter, we kunnen ze meer diep raken"). Not advice, recognition. The arc:
  1. you: a raw 2am confession with one concrete detail (an age, a habit, a moment), something people never say out loud. Not a neutral "Why do I...?" question.
  2. ladder: a short reframe that names what is really going on, max about 8 words ("You're not behind. You're auditing.").
  3. you: the pain behind it, or a scared follow up ("What if they leave when they see the rest?").
  4. ladder: the line that hurts, taken almost word for word from the book (Adriaan's strongest sentences: "you were somewhere else while it happened", "a version of yourself that only exists as an idea", "guilt has never once kept a promise", "old pain signing your name to choices you never made", "they loved the edited cut", "cheap wants never cost you anything, that's why they never build anything").
  5. you: quiet surrender ("So what do I do?").
  6. ladder: permission plus one small true step, ending on a line worth a screenshot. Max about 14 words.
  Example approved direction: 2026-11-13-deep-1 "The edited version" (People like me. But only the version I let them see.). Labels name the feeling, not a textbook term.
- Variety: every video a different chapter and a different named idea; read earlier labels and hooks in log.csv (label goes in the clip column as "dialog: <label>").

## Ladder text format from 2026-11-12 morning (REPLACED the same evening by the ladder dialog above)
Adriaan sent the ladder remake of 2026-11-08-2 ("Your wants are too cheap.") and said: make ALL videos like this one. First batch in this format: 2026-11-12-1 to -4.
- Spec values: "beat": 1.0 (60 BPM), "minlen": 4, "size": 48 (small text, no "hook_size"), "x": 96, "y0": 830, "ladder": true, "climb": 50, black and white ("pre" starts with "hue=s=0,"), "blob" at least 0.45. Never "label", never "cta". Mode loop, or book with "outro_cta": false on even days for video 4.
- Length 18 s: 4 blocks; blocks 1 to 3 have 2 lines, block 4 has 3 lines (third line gold). The text climbs one step per block and the ladder on the left lights up one rung per gold line.
- Lines at size 48: keep x + width under about 900 px (about 32 characters). Hook is a normal size first line, on screen from frame 1.
- Footage: near black aerial night highways and roads, like the reference (pex-28698188, pex-11372905, pex-11326269, pex-28698336, pex-11372907). Prefer clips of at least 14 s so they don't get slowed down much; driving POV clips are fine too.
- Sound: around 60 BPM (or 120) so the gold lines land on the beat.
- VARIETY (Adriaan 2026-11-12: "er is genoeg te vertellen in het boek, dus niet de hele tijd dezelfde dingen"): rotate over all chapters in book.txt, including Part Five (True Freedom, The Art of Boredom, The Art of Detachment, The Art of Resistance, Your True Freedom, Conclusion). Before writing, read every earlier hook from that chapter in log.csv and pick a DIFFERENT passage and idea, not a reworded version of an earlier angle (the Gap, the parent/model and "that thought isn't you" angles have been used many times). Vary the shape too: not every hook a "You're not X" line; also commands, concrete lists and questions.
- toolkit/reference/book.txt was replaced on 2026-11-12 with Adriaan's latest PDF (five Parts, 17 chapters).

## Winner check (Adriaan, 2026-11-11)
- 2026-11-08-2 "Your wants are too cheap. / They never cost you anything." (Price Tag chapter, pex-28698188, near black aerial highway, B&W) is still doing better than the newer videos, including the flash format tests. It is the OLD format: about 18 s, small text (size 48), 60 BPM, 4 blocks, one calm clip.
- Adriaan wants a recognisable signature for the account (one fixed visual setup, a different quote each time). Not decided yet.

## Flash format test (Adriaan, 2026-11-11, liked the first one)
- One book quote in 2 lines (hook from frame 1, gold second line), over a montage that cuts every 0.75 s (80 BPM): Adriaan's rainy night photos (slow zoom) alternated with driving clips, black and white, about 9.75 s, seamless loop.
- Build: segments with frame exact cut points (first segment 1.35 s because loop mode trims 0.6 s), concat to one montage, then reel.py with that montage as clip, "minlen": 12, one block. Photos are in the session uploads, not in git.
- Waiting for numbers: compare with the 13.5 s default.

## Old default from 2026-11-09 (REPLACED on 2026-11-12 by the ladder format above)
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
