from PIL import Image
import sys, os

class pvdExtract:
    def __init__(self, output_file):
        self.output_file = output_file

        # File Objects creation
        self.im = Image.open(self.output_file)
        self.outp = open(os.getcwd() + '/webapp/algorithms/pvd/temp', "w+")
        self.lg = open(os.getcwd() + '/webapp/algorithms/pvd/embedlog.log', "r")

        # Initialisation
        self.pix = self.im.load()
        self.temp = 1
        self.chrtr = ""

    # Main Function
    def extract(self):
        while True:

            # Read each line from log file
            st = self.lg.readline()

            # Check if log file reached its end
            if len(st) == 0:
                # Write extracted data to file
                # print(chr(int(chrtr, 2)))
                self.outp.write(chr(int(self.chrtr, 2)))
                break

            # Unpack line read from log file to variables
            i, j, pixel, diff, pad, charNum = st.split()

            # Process variables
            i = int(i)
            j = int(j)
            diff = int(diff)
            pad = int(pad)
            charNum = int(charNum)
            r, g, b = self.pix[i, j]

            # Check if a new character in embed log is reached
            if self.temp != charNum:
                # print(chr(int(chrtr, 2)), end="")
                self.outp.write(chr(int(self.chrtr, 2)))
                self.chrtr = ""

            # If embedded pixel is red
            if pixel == "r":
                binr = bin(r)
                self.chrtr += binr[(len(binr) - diff) :]

            # If embedded pixel is green
            if pixel == "g":
                binr = bin(g)
                self.chrtr += binr[(len(binr) - diff) :]

            # If embedded pixel is blue
            if pixel == "b":
                binr = bin(b)
                self.chrtr += binr[(len(binr) - diff) :]

            # Unpad if padding is done
            if pad != 0:
                self.chrtr = self.chrtr[: (len(self.chrtr) - pad)]

            # For checking if character has changed in embed file
            self.temp = charNum

        # Close file objects
        self.outp.close()
        self.lg.close()
        self.outp = open(os.getcwd() + '/webapp/algorithms/pvd/temp')
        return self.outp.read()
