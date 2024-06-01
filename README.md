DEPRECATED PROJECT: see [Playful Plugins](http://furimanejo.itch.io/playful-plugins) for an up-to-date version of this mod.

An application to controls sex toys based on Helldivers 2 gameplay. Here's a [list](https://iostindex.com/?filter0ButtplugSupport=4) of supported devices.

# Instructions:
- Install and run [Intiface Central](https://intiface.com/central/).
- Download a release of [Hornydivers](https://github.com/Furimanejo/Hornydivers/releases) (the .zip file, not the Source Code) and extract it to a new folder. Do not move the files from inside it.
- Run Hornydivers. On the tab "Device Control" click connect to intiface. Make sure your toys are on and appear on the list of connected devices.
- Test the app by playing Helldivers 2, or a gameplay video in fullscreen.

# Current Features:
- Hornydivers reads your screen while you play, detecting changes on the game's HUD and generating a score that is used to control your toys.
- You get points when your health goes up or down, proportional to the amount of health changed. These points go down over time according to the decay value.
- You also have points proportional to your current missing health. These don't decay with time.

# Observations:
- Only the default HUD settings are supported (Scale = 0.90 and Curve = 0).
- Supported aspect ratios: 16:9.
- To use the overlay make sure your game is running in borderless display mode.
- For multiple monitors setups: you can change the montitor where the detection occurs by editing the variable "monitor_number" in the generated config file "config.json".

# Support:
Join my [discord server](https://discord.gg/wz2qvkuEyJ) if you have any questions, suggestions or just wanna talk about related stuff.

And if you liked the app and want to support me, you can donate at https://donate.stripe.com/7sI3eZcExdGrc5WeUU
