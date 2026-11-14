# The Ladder Formula (from 2026-11-14, binding for every video)

Goal per video: people stop in the first second, stay until the gold ending, save the method and comment.
Every spec is scored with `python3 toolkit/score.py SPEC.json` before rendering. Below 80 points: fix it, don't render.

## Where these rules come from
- TikTok confirms that what users do with a video counts most: watch time, completion, rewatches, shares, comments, follows. Skips count against it. Follower count is not a factor. ([meikuio](https://meikuio.com/tiktok-algorithm-2026/), [Hootsuite](https://blog.hootsuite.com/tiktok-algorithm/))
- Benchmarks (marketing data, rough): 3 second hold 60 to 65%+ to get pushed past the first test pool. Midpoint hold 45%+. Completion on a 30 s video 25 to 35%+. Big drop off points sit around 3 s and 12 s. ([grow-it](https://www.grow-it.se/en/resources/short-form-video-retention-benchmarks), [Opus](https://www.opus.pro/blog/tiktok-hook-formulas))
- Something new on screen every 2 to 3 s. No single frame holding for 8 s. ([grow-it](https://www.grow-it.se/en/resources/short-form-video-retention-benchmarks), [gofaceless](https://www.gofaceless.ai/blog/optimize-video-engagement-pattern-breaks))
- Kinetic text with each line landing on the beat and the key line on the drop is the format that holds the most content. Numbered lists keep people watching to the end. ([HookClone](https://www.hookclone.com/blog/trending-tiktok-formats-2026))
- Comments come from either/or, pick a number, "am I wrong?" and a strong opinion. "Comment to unlock" style bait gets punished. ([Socialync](https://www.socialync.io/blog/increase-tiktok-comments-engagement-2026))
- Muting a trending sound to 0% to borrow its reach does not work. TikTok reads the real audio. ([meikuio](https://meikuio.com/tiktok-algorithm-2026/))

## 1. Hook (0 to 2 s), 25 points
- On screen in frame 1, spoken from 0.12 s, max 8 words, done before 2.3 s.
- Talks to "you" and stings: a claim people want to argue with, or a pain they recognise. Rotate the 4 types and write the type in the spec (`"hook_type"`):
  - `claim`: "Your goal has no edges."
  - `stop`: "Stop saying your goals out loud."
  - `question`: one specific question. "Why do you quit every plan on day 4?"
  - `proof`: Adriaan's own result. "I wrote my goal on a card. 90 days later..." (best for trust; ask Adriaan for real numbers)
- Motion in the first 0.5 s (something draws, drops or slams in). Never a still opening frame.

## 2. Open loop (2 to 16.4 s), 10 points
- Within 5 s, promise what they'll get: "Here's the 4 step rule." People who know a list is coming stay to the end.
- Show the problem with the metaphor. End on a question right before the silence at 16.4 s. The drop answers it.

## 3. Pacing (the whole video), 20 points
- Something visibly changes at least every 2.5 s: a new object, a text swap, a camera punch (`"punch": true`), a step.
- The words on screen change with the voice. Max 7 words per screen in the build, max 5 words per step.
- One place to look: the key word sits on or right next to the picture, not only at the top.

## 4. Payoff on the drop (17.18 s), 20 points
- A named, numbered method: one step per beat, steps of 2 to 5 words.
- After the steps, show the full list for at least 3 s (the screenshot and save moment).
- Concrete examples next. Real ones from Adriaan's life beat made up ones.

## 5. Emotion, gold and loop (after 36.8 s), 10 points
- One line that hurts, almost word for word from the book.
- The gold moment, then the last spoken line leads back into the hook so the video loops (a rewatch counts as watch time).

## 6. Comment engine, 15 points
- The video ends with a question that is easy to answer in one word, spoken and on screen (`"comment_q"`):
  - pick a number: "Which step do you skip? 1, 2, 3 or 4?"
  - either/or: "Cloud or box: what's your goal right now?"
  - fill in: "Write your goal with a number and a date."
- The same question goes in the pinned comment. "Comment BOOK" stays only in the caption, never in the video.
- Adriaan: reply to the first comments within 30 minutes, ideally with a video reply. That's the cheapest reach there is.

## 7. Music
- Rotate trending sounds instead of one track for everything. Every week Adriaan sends 2 or 3 sounds he likes from the For You page, as a saved video or screen recording. We measure each one with `python3 toolkit/beatmap.py SOUND.mp4 toolkit/sounds/<name>.json` and the spec picks it with `"sound": "<name>"`. VYZEE stays as `"sound": "vyzee"`.
- Pick sounds with a clear build and drop. Good fits right now: "Movin' To The Sun" (HUGEL), "Free Your Mind" (Prospa & Cloonee), "Rise Slow" (Kimo Sounds), "LEGACY" (PIXY). ([SoundMatcha, 7 Nov 2026](https://soundmatcha.com/tiktok/)) Check the real audio before using one.
- In TikTok: "Use this sound" from 0:00, voice about 100%, music about 30 to 40%. On Reels use the same sound if it's there. On Shorts use the Shorts audio library.

## 8. Measure and adjust (the loop that makes it work)
- After 48 h Adriaan sends the TikTok Studio screenshots (retention graph, average watch time, watched full video, likes, comments, saves, shares, new followers). They go in `results.csv`.
- Targets: 3 s hold 60%+, watched full video 25%+, comments 0.5%+ of views, saves 1%+ of views.
- Every Sunday: compare the hook types, sounds and metaphors. Do more of the winner and drop the bottom 25%. Write the result in lessons.md.
