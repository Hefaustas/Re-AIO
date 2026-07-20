# Re: Attorney Investigations Online

Re:AIO is WIP a reimplementation of the [original Attorney Investigations Online client](https://github.com/headshot2017/AIO#), with added features and bug fixes.

[Attorney Investigations Online](https://aai-online.github.io/help/) is an online multiplayer version of the Capcom spin-off series "Ace Attorney Investigations: Miles Edgeworth".

This is written in Python 3.10+

Instead of PyQt4, this project utilizes PySide6 for the GUI.

### Roadmap

- [ ] First (easy?) features
    - [x] Project scaffolding (Build the basic structure of the project)
        - [x] Wire Application to MainWindow, use stacked widgets
        - [x] Decide on Python 3 libraries 
    - [x] Port the complete UI (pre-join) from PyQt4 to PySide6
        - [x] Lobby
        - [x] Settings
        - [ ] ~~About~~ (On first release)
        - [ ] ~~News~~ scrapped (I don't think anyone reads this.)
        - [x] Join IP dialog
        - [x] * Favorites list (The UI is there but not functional)
    - [x] * Audio backend (BASS)
        - [ ] BassOPUS needs to be figured out.      
    - [x] Functional settings dialog (with saving to config file)
        - [x] Settings UI
        - [x] Rendering and saving settings from config
    - [ ] Lobby UI and connect flow
- [ ] Networking and gameplay foundation
    - [ ] In-game UI (?)
    - [ ] Implement UDP client thread and master server query
    - [ ] Server list and joining
    - [ ] In-game chat
    - [ ] Favorites management
    - [ ] News functionality
    - [ ] Multiplayer protocol
    - [ ] Server/Client communication
    - [ ] Asset loading
    - [ ] Basic server
    - [ ] Ability to join games
    - [ ] Master server
- [ ] Gameplay
    - [ ] Finish in-game UI
    - [ ] Viewport rendering
    - [ ] Chatbox
    - [ ] Player movement and emotes
    - [ ] Implement new collision system
    - [ ] Zones
    - [ ] Musiclist functionality
    - [ ] Character select
    - [ ] Evidence window
- [ ] Server-side
    - [ ] Server configuration
    - [ ] Server commands?
        - [ ] Player management (kicking, banning, muting)
    - [ ] IC, OOC chat handling
    - [ ] Modpass
- [ ] Advanced
    - [ ] Clean up code?
    - [ ] Close-up chat
    - [ ] Finalise unreleasd 0.5 features (.ini offsets, shadows, etc.)
    - [ ] add ability to pick spin.gif (similar to run adn walk anim)

I'm not too sure how feasible some of these are, nor where they should actually be placed but it's a start.
    
