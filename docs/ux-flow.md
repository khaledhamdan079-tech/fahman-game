# UX and screen flow

## Design direction

The Arabic identity is **فهمان**. The interface is RTL-first and
uses a modern game-show tone without copying the reference product's branding.

Principles:

- The current turn must be unmistakable.
- Scores remain visible during board and question states.
- Point tiles are large and usable from a phone or tablet placed on a table.
- Used questions remain visible but disabled.
- Lifelines show available, armed, and used states.
- Media controls are simple: play, replay count, progress, and duration.
- The game board prefers landscape orientation on phones and tablets.
- All state-changing actions provide a clear confirmation or undo-safe step.

## Screen flow

```text
Splash
  -> Automatic installation setup
  -> Home
      -> New match
          -> Choose category count
          -> Choose categories
          -> Enter team names
          -> Review rules
          -> Game board
              -> Optional pre-open Double points
              -> Question
                  -> Media preload
                  -> Play + timer
                  -> Optional Show options / Block opponent
                  -> Reveal answer
                  -> Choose scoring team / No one
                  -> Game board
              -> Final result
      -> Match history
          -> Match details
      -> Profile and question availability
```

## Game board

- Header: match progress and pause action
- Team score panels: active team uses the primary accent
- Category columns: six point tiles per category
- Point tile: value, optional media-type icon, and used state
- Footer: three lifelines for the active team

Showing a small image/audio/video icon on a tile is recommended. It lets the
host anticipate playback requirements while keeping the actual prompt secret.

## Text question

- Category and points
- Countdown
- Prompt
- Two to four ordered options
- Lifelines valid for the current state
- Reveal answer action

## Image question

- Image fitted without cropping important details
- Tap-to-expand on smaller screens
- Prompt and options below the image
- Loading must finish before the countdown begins

## Audio question

- Prompt appears before playback
- Large play button
- Progress and duration
- Remaining play count, default two
- No seek control in the first release
- Timer begins with the first successful playback

## Video question

- Poster frame until play
- Play/pause, progress, duration, and remaining play count
- No arbitrary seek control
- Clip stops at its authored endpoint
- Options may appear immediately or at clip completion, configurable per
  question

## Reveal and scoring

After Reveal answer:

- Correct answer is highlighted.
- Media stops and cannot restart.
- Three adjudication actions appear: Team 1, Team 2, No one.
- Blocked teams are disabled with an explanation.
- A final confirmation shows the exact score change before committing.

## Recovery states

- If connectivity drops, keep the visible question but disable scoring actions.
- On reconnect, fetch the server match state before accepting another command.
- If media fails before playback, retry; after repeated failure, replace the
  question through a server command without marking it used.
- On app restart, offer Resume match when an active match exists.

## Accessibility

- Maintain strong color contrast and never rely on color alone.
- All controls have Arabic semantic labels.
- Images have neutral descriptions that do not reveal the answer.
- Captions or transcripts can be revealed after scoring when providing them
  before the answer would spoil the question.
- Sound is never the only signal for timer expiry.
