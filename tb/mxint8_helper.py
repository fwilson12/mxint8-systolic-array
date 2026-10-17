import random   
import math

def getE(block: list[int]) -> int:
    # find & return the microscaled block (biased) exponent of a block of integers

    bigNum = block[0] # used to avoid unnecessary calculations
    bigE = math.floor(math.log2(abs(block[0]))) # stores the block exponent, determined by the greatest power of two we can divide each value by : the quantized block values are within [-2, ~1.95)
    
    for i in range(1, len(block)):
        if block[i] > bigNum:
            bigNum = block[i]
            bigE = math.floor(math.log2(abs(block[i])))

    return bigE + 127


def quantize(block: list[int], exp: int) -> list[float]:
    # scale each block | note: exp is biased w/ 127

    mxBlock = [] * 32
    mxBlock = [num / 2**(exp - 127) for num in block]

    return mxBlock



def mxDotProd(wBlock: list[int], aBlock: list[int], eW: int, eA: int) -> float:
    # calculate the dot product of a weight and activation block 

    unscaledProd = [weight * activation for weight, activation in zip(wBlock, aBlock)]

    return unscaledProd * 2**(eW + eA - 266) # - 254 (bias) - 12 (microscale)




# n - 1 activation layer -> microscale -> dot prod with microscaled weights -> collect unscaled ints -> unscale