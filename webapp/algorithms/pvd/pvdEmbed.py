from PIL import Image
import sys, os

class pvdEmbed:
    def __init__(self, input_file, output_file, secret):
        self.input_file = input_file
        self.output_file = output_file

        # File Objects creation
        temp = open(os.getcwd() + '/webapp/algorithms/pvd/temp', "w+")
        temp.write(secret)
        temp.close()
        self.input = open(os.getcwd() + '/webapp/algorithms/pvd/temp', "r")
        self.im = Image.open(self.input_file)
        self.lg = open(os.getcwd() + '/webapp/algorithms/pvd/embedlog.log', "w")

        # Initialisation
        self.pix = self.im.load()
        self.hi, self.wi = self.im.size

        self.completed = 0
        self.retrieved = ""
        self.count = 0
        self.paddbits = "0000000"

        self.binval = self.input.read(1)
        self.charNum = 1
        if len(self.binval) == 0:
            print("\nEmpty i/p File!")
            sys.exit("Exiting...")
        self.b = ord(self.binval)
        self.bitstring = bin(self.b)
        self.bits = self.bitstring[2:]

        self.capacity = 0
        self.lix = self.hi // 3
        self.liy = self.wi // 3

    # Classify pixels based on the difference in pixel value to the number of bits to be substituted to LSB
    def classify(self, pvd):
        nbits = 0
        if pvd < 16:
            nbits = 2
        elif 16 < pvd < 32:
            nbits = 3
        else:
            nbits = 4
        return nbits


    # Calculate embedding capacity of the given cover image
    def calcCapacity(self):

        # Divide pixels to [3 x 3] matrix
        for i in range(0, self.lix * 3, 3):
            for j in range(0, self.liy * 3, 3):

                # Obtain pixel values of ref. pixel
                rref, gref, bref = self.pix[i + 1, j + 1]

                # For all pixels in the matrix
                for k in range(i, (i + 3)):
                    if k >= self.hi:
                        break
                    for l in range(j, (j + 3)):
                        if k == i + 1 and l == j + 1:
                            continue
                        if l >= self.wi:
                            break

                        # Calculate the difference in pixel values
                        r, g, b = self.pix[k, l]
                        rdif = r - rref
                        gdif = g - gref
                        bdif = b - bref
                        rdif = abs(rdif)
                        gdif = abs(gdif)
                        bdif = abs(bdif)

                        # Cumulative capacity
                        self.capacity = (
                            self.capacity + self.classify(rdif) + self.classify(gdif) + self.classify(bdif)
                        )

        # Return capacity
        return self.capacity


    # Function to embed data to pixel
    def embedbits(self, i, j, pixel, diff, colorpixel):
        # Initialise
        pad = 0
        nb = diff

        # If the number of bits required is less than the number of bits in the data(char.) to be Embedded
        if nb < len(self.bits):

            # Initialise
            newbits = self.bits[:nb]
            self.bits = self.bits[nb:]
            val = colorpixel
            data = newbits
            bival = bin(val)
            bival = bival[2:]
            newbival = bival[: (len(bival) - len(data))] + data

            # Write data to log File for extraction
            self.lg.write("%s %s %s %s %s %s %s" % (i, j, pixel, diff, pad, self.charNum, "\n"))

            # Return new pixel value after embedding
            return int(newbival, 2)

        # If the number of bits required is greater than the number of bits in the data(char.) to be Embedded
        else:

            # Apply padding
            newbits = self.bits + self.paddbits[: (nb - len(self.bits))]
            pad = nb - len(self.bits)
            val = colorpixel
            data = newbits
            bival = bin(val)
            bival = bival[2:]
            newbival = bival[: (len(bival) - len(data))] + data
            self.count += 1

            # Write data to log File for extraction
            self.lg.write("%s %s %s %s %s %s %s" % (i, j, pixel, diff, pad, self.charNum, "\n"))

            # Read new char. for embedding
            binval = self.input.read(1)

            # Check if file containing data to embed reached its end
            if len(binval) == 0:
                print("Embedding Completed")

                # Close input file object
                self.input.close()

                # Activate complete flag
                self.completed = 1

                # Return new pixel value after embedding
                return int(newbival, 2)

            # Check if file containing data to embed havent reached its end
            b = ord(binval)
            bitstring = bin(b)
            self.bits = bitstring[2:]
            self.retrieved = ""

            # Increment the char count of embedded data
            self.charNum += 1

            # Return new pixel value after embedding
            return int(newbival, 2)


    # Main Function
    def embed(self):

        # Initialise counter containing num of bits embedded till embedding ends
        embedded = 0

        # Print total Embedding capacity
        print("Total Embd. Capacity: ", self.calcCapacity())

        # Divide pixels to [3 x 3] matrix
        for i in range(0, self.lix * 3, 3):
            for j in range(0, self.liy * 3, 3):

                # Obtain pixel values of ref. pixel
                rref, gref, bref = self.pix[i + 1, j + 1]

                # For all pixels in the matrix
                for k in range(i, (i + 3)):
                    if k >= self.hi:
                        break
                    for l in range(j, (j + 3)):
                        if k == i + 1 and l == j + 1:
                            continue
                        if l >= self.wi:
                            break

                        # Calculate pixel value difference
                        r, g, b = self.pix[k, l]
                        rdif = r - rref
                        gdif = g - gref
                        bdif = b - bref
                        rdif = abs(rdif)
                        gdif = abs(gdif)
                        bdif = abs(bdif)

                        # Till embedding gets completed
                        if self.completed == 0:
                            newr = self.embedbits(k, l, "r", self.classify(rdif), r)
                        if self.completed == 0:
                            newg = self.embedbits(k, l, "g", self.classify(gdif), g)
                        if self.completed == 0:
                            newb = self.embedbits(k, l, "b", self.classify(bdif), b)

                        # Embedding completed
                        if self.completed == 1:

                            # Assign modified pixel values
                            self.pix[k, l] = (newr, newg, newb)

                            # Save embedded image
                            self.im.save(self.output_file)

                            # Close log file
                            self.lg.close()
                            print("Embedded:", embedded, "bits")
                            return

                        # Calculate the number of bits embedded
                        embedded = (
                            embedded + self.classify(rdif) + self.classify(gdif) + self.classify(bdif)
                        )

                        # Assign modified pixel values
                        self.pix[k, l] = (newr, newg, newb)
        return
