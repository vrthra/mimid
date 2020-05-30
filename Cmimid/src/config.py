import os, string
RandomSeed = int(os.getenv('R') or '0')

MyPrefix = os.getenv('MY_PREFIX') or None

#  Maximum iterations of fixing exceptions that we try before giving up.
MaxIter = int(os.getenv('MAX_ITER') or '10000')

# When we get a non exception producing input, what should we do? Should
# we return immediately or try to make the input larger?
Return_Probability =  float(os.getenv('MY_RP') or '1.0')

# The sampling distribution from which the characters are chosen.
Distribution='U'

Debug=1

TIMEOUT = 10

eof_char = chr(126)

No_CTRL = (os.getenv('NOCTRL') or 'false') in ['true', '1']

All_Characters = list(string.ascii_letters + string.digits + string.punctuation) \
        if No_CTRL else list(string.printable)
All_Characters = [i for i in All_Characters if i not in {"\n"}]
