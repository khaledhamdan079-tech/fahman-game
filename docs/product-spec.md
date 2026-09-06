# Product specification

## Product statement

Fahman (فهمان) is an Arabic trivia game for two teams playing together on one
host device. The game combines a category board, escalating point values,
one-time tactical lifelines, multimedia questions, and persistent history.

The first release is intentionally local and host-controlled. Multi-device
rooms and tournaments are later features.

## Match setup

1. The signed-in host chooses between 3 and 7 categories.
2. The host enters both team names.
3. Each team receives the same three lifelines:
   - Two answers
   - Double points
   - Block opponent
4. The timer defaults to 60 seconds. A later settings control may allow 30–90
   seconds.
5. The backend atomically reserves the questions and creates the match.

## Question distribution

Every selected category contributes exactly six questions:

- Two questions worth 200 points
- Two questions worth 400 points
- Two questions worth 600 points

This creates 18–42 questions per match.

A category is eligible only when the user has at least two unused questions at
each point level. The category response also exposes:

- Unused 200-point count
- Unused 400-point count
- Unused 600-point count
- Total unused count
- Number of complete future matches possible, calculated as the minimum of
  `floor(unused_at_level / 2)` across the three levels

Questions are reserved when a match is created, but become used only when the
question is opened. If a match is cancelled or expires, unopened reservations
are released; already opened questions remain used.

There is no automatic question recycling in the first release. A deliberate
"reset used questions" feature can be added later.

## Question formats

Every question has one of four types:

- `text`: prompt and options only
- `image`: one image plus prompt and options
- `audio`: a short sound clip plus prompt and options
- `video`: a short clip plus prompt and options

Examples:

- "Which car makes this sound?"
- "Which city is shown in this image?"
- "Complete this famous scene."
- "Who is speaking in this audio clip?"

The content record stores the real answer and ordered options. Teams may answer
verbally; after revealing the answer, the host selects Team 1, Team 2, or No
one. The backend applies points based on that adjudication.

## Media playback rules

- Flutter preloads the media before the question becomes playable.
- The countdown starts only after Flutter reports the media ready and playback
  begins. Network buffering must not consume answer time.
- Audio and video allow two plays by default. The limit is recorded per match
  question and enforced by the backend.
- Showing the answer stops playback and disables further plays.
- Video clips should be pre-edited to end at the intended question moment.
- The original file name and storage path are never exposed to the player.
- A failed media load allows retry or replacement of the question without
  consuming it.

Recommended content limits for the first release:

- Images: WebP, JPEG, or PNG; target maximum 2 MB
- Audio: M4A/AAC, MP3, or OGG; target maximum 20 seconds
- Video: MP4 with H.264 video and AAC audio; target maximum 30 seconds

All film, television, music, and other copyrighted media must be licensed,
original, or in the public domain. The safest launch catalogue uses original
sounds, owned recordings, and licensed clips.

## Turn flow

1. The current team may activate Double points before choosing/opening the
   question.
2. The current team chooses one available question.
3. The backend opens it and returns its playable content.
4. Flutter waits for any media to become ready, starts playback, then begins
   the timer.
5. Two answers or Block opponent may be activated after the question is open
   and before the answer is revealed.
6. The host reveals the answer.
7. The host selects Team 1, Team 2, or No one.
8. The backend calculates the score, closes the question, and changes the turn.
9. The teams alternate turns regardless of which team answered correctly.

## Lifelines

### Two answers

- Usable once per team per match.
- Activated after the question opens and before the answer is revealed.
- Allows the current team to give or select two possible answers.

### Double points

- Usable once per team per match.
- Must be activated before the question opens.
- Applies to one question only.
- Doubles the award for a correct answer.
- Does not create a penalty for an incorrect answer in the first release.

### Block opponent

- Usable once per team per match.
- Activated after the question opens and before the answer is revealed.
- Prevents the opposing team from receiving points for that question.
- If the current team is incorrect, the result is No one.

## Timer

- Default duration: 60 seconds
- The backend records authoritative `opened_at`, `media_ready_at`, and
  `deadline_at` timestamps.
- Flutter renders a smooth local countdown from the backend deadline.
- Revealing the answer freezes the timer.
- Expiry does not change scores automatically; the host still records the
  result.

## Match completion

The match finishes when every reserved question is scored. The backend stores:

- Team names and final scores
- Winner or draw
- Selected categories
- Question snapshots and results
- Lifelines used
- Start and finish timestamps
- An ordered event log for audit and recovery

## Explicit MVP assumptions

- One signed-in host owns and controls the match.
- Both teams share one device.
- The host adjudicates who answered correctly.
- No negative points.
- No real-time remote rooms.
- No purchases, subscriptions, gifts, or tournaments.
- Content administration begins with validated CSV/JSON import plus media
  upload tooling; a full admin dashboard comes later.
