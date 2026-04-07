# cowboard

*cowsay, but it sticks.*

A persistent sticky-note board for your terminal, powered by ASCII animals.
Zero dependencies. Pure bash. Works everywhere.

---

## Who is this for?

**Terminal lifers** — sysadmins, DevOps engineers, backend developers who live in
the shell all day and want a scratchpad that lives there too.

**cowsay fans** — if you have `fortune | cowsay` in your `.bashrc`, this is the
natural next step. Same aesthetic, now persistent and interactive.

**tmux users** — pin cowboard in a pane. Glance at your notes while you work.
No context switching, no alt-tab, no browser tab.

**Unix toyware collectors** — if you have `sl`, `cmatrix`, `cbonsai`, or
`pipes.sh` installed, you need this.

**r/unixporn regulars** — it looks great in a screenshot.

---

## The pitch

You open your terminal. Your notes are already there.

Not in a browser. Not in a separate app. Not in a file you have to `cat`.
Right there, with a dragon, a penguin, or a cupcake holding them.

Type `/tux Deploy done` and Tux appears with your note.
Type `/dragonr URGENT` and a red dragon shouts it at you.
Type `/clear` when you're done.

Resize the terminal — the notes reflow. Close and reopen — the notes are still there.

---

## Why it spreads

- **One-line install** — no npm, no pip, no brew. Just bash.
- **~50 built-in animals** — cow, dragon, tux, cupcake, turtle, turkey, ghost, and more.
- **Coloured notes** — append `g` `r` `b` `y` to any animal for green, red, blue, yellow.
- **Smart layout** — masonry column layout that adapts to your terminal size.
- **Tab completion** — `/` + Tab shows all commands and animal names.
- **Interactive animal picker** — `/animals` opens a full-screen grid, arrow keys to browse.
- **History** — arrow up/down through previous commands, persisted across sessions.

---

## Where to find the audience

| Channel | Why it works |
|---|---|
| Hacker News "Show HN" | Terminal toys do well; cowsay has 25 years of goodwill |
| r/unixporn | Screenshot with a nice theme = instant upvotes |
| r/commandline | Direct audience |
| r/bash | They'll appreciate the pure-bash implementation |
| lobste.rs | Curated Unix crowd |

---

## The demo GIF

Show these four moments:

1. `/dragon Deploy done` — dragon appears
2. `/tuxr URGENT` — red Tux appears beside it
3. Resize the terminal — notes reflow live
4. `/animals` — full-screen picker with arrow navigation

Ten seconds. That's the whole pitch.

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/youruser/cowboard/main/cowboard.sh -o cowboard.sh
chmod +x cowboard.sh
./cowboard.sh
```

Or add to your path:

```bash
mv cowboard.sh ~/.local/bin/cowboard
cowboard
```
