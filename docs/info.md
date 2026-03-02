<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

Quick Draw is a two player game where players compete to flip a switch after a light turns off. The game begins after one player flip the GO switch to start a round. A green light will turn and an 8 bit LFSR loads a random value into a counter that ticks every quarter second. When the counter hits zero the green light turns off. The first player to flip their switch after the light goes off wins the round. If a player flips before the light goes off then the other player wins. If both flip at the same time before the light, both lose. If both flip at the same time after the light, both win a point.

The game uses is a 7 state one hot FSM with the following states:

IDLE, GREEN_ON, GREEN_OFF, BOTH_LOSE, B_WINS, BOTH_WIN, and A_WINS

Scores are tracked using two 3 bit counters. The first player to reach 3 points wins that game and a player can restart the whole game by presing reset.


## How to test

Switch 0 is Player A
Switch 1 is Player B
Switch 2 is GO
Switch 3 is the cheat switch

Flip the GO switch up to start a round. The 7-segment display will go blank while the countdown runs. When the display is blank and the green light signal goes low players can now compete to flip the switch first. The display will show the score.

Use the cheat switch to test simultaneous flips flipping it while the green light is on tests the both lose scenario, and flipping it after the light goes off tests the both win scenario.

Play until someone reaches 3 points.

Game over ligths are uio[5] and uio[6] and will light up to signal the winner.

Finally, Reset with rst_n to clear all scores and play again

