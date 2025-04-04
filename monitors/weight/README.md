# Keg Volume Weight Monitor

Inspired by the now discontinued Plaato keg, this monitor uses the weight of the keg over time ter determine the current
 volume based on the weight of the empty keg and the weight of a full keg.  I love the Plaato keg, and was sad when they
 annouced their pivot away from home brewing gear and would no longer be selling, innovating or supporting the Plaato
 keg.  In my search I found a few other DIY clones using low cost hardware and existing technologies.  However, I wanted
 to build some truly DIY and fully opensource.  So I designed my own keg scale using the Particle Photon 2 platform.

![alt text](_img/weight_circuit.png "Title")

## Parts required

- [Particle Photon2](https://store.particle.io/products/photon-2) (optionally will work with discontinued Photon or Argon)
- [4 Load Cells w/ HX711 amplifier](https://www.amazon.com/Bridge-Digital-Amplifier-Arduino-DIYmalls/dp/B086ZHXNJH)
- Micro USB cable
- [5mm RGB Led (common cathode)](https://www.amazon.com/PATIKIL-Emitting-Mounting-Bracket-Transparent/)
- 3X 330 ohm Resistor
- [5mm LED holder](https://www.amazon.com/PATIKIL-Emitting-Mounting-Bracket-Transparent/dp/B0C54Y99NQ)
- (OPTIONAL) [6mmX6mm single pole push button switch](https://www.amazon.com/dp/B07WF76VHT) + 1 10k Ohm resistor

## Links

- [Another DIY Plaato Keg clone](https://www.youtube.com/watch?v=QF1B8yD9jy4) from the [Trouble Brewing](https://www.youtube.com/@TroubleBrewing) 
YouTube channel.  This one uses a NodeMCU 8266 module and Home Assistant Server.  However, I am not a huge fan of these modules or Home Assistant
and I wanted to build something fully opensource.
- [Wiring up and calibrating HX711 with 4 load cell using arduino](https://www.youtube.com/watch?v=LIuf2egMioA)