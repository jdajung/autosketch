This is the code for the drawing application associated with the paper "Automating the Intentional Encoding of Human-Designable Markers" by Joshua Jung, Rahul iyer, and Daniel Vogel, published at CHI 2019. It requires Python 2.7, OpenCV, and all of OpenCV's dependencies to run.

To run the application, download all files and dependencies, open a terminal, navigate to the project directory, and enter the following command:

python application.py

<br><br>

Optionally, you may specify a target encoding using one of the following commands, where the last token should be replaced with your desired encoding:

python application.py 10001   (encoding of 10001 in binary)

python application.py -2 10001   (also encoding of 10001 in binary)

python application.py -10 17   (encoding of 17 in decimal)

python application.py -36 g    (encoding of G in base 36 [i.e. 17 in decimal])

<br><br>

The drawing application accepts the following keyboard shortcuts:

escape - closes the program

1 - changes draw colour to black

2 - changes draw colour to white (i.e. erase)

\+ or > - increases size of brush

\- or < - decreases size of brush

z - does one undo

shift+z - does one redo

shift+c - clears the canvas

tab - toggles the labelling tool

space - toggles the ordering tool

a - toggles the ambiguity tool

o - toggles the contour tool

m - change encoding modes

shift+s - saves the current canvas as a PNG

shift+l - loads the last saved PNG (WILL CLEAR THE CURRENT CANVAS, but is undoable)

shift+f - same as shift+s, but enters a 'failure' code in the log (used in study, but otherwise not needed)

shift+p - same as shift+s, but enters a 'practice' code in the log (used in study, but otherwise not needed)

shift+g - generate a random bitstring of length 10 (used in study, but otherwise not needed)

shift+h - generate a random bitstring of length 20 (used in study, but otherwise not needed)