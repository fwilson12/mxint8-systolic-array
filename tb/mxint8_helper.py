import random   
import math


BLOCK_SIZE = 16
LOW_BOUND = -127 # while the minimum value in Q2.6 is -2, for symmetry we forbid the use of 
UPPER_BOUND = 127

EXP_BIAS = 127
FRAC_BITS = 6


def clamp(min, max, num):
    # helper that saturates integer-formatted values to a specified range
    return min if num < min else (max if num > max else num)

def getE(vector: list[int]) -> int:
    # find & return the microscaled block (biased) exponent of a block of integers

    bigNum = max(abs(comp) for comp in vector) # used to avoid unnecessary calculations
    bigE = math.floor(math.log2(bigNum)) # stores the block exponent, determined by the greatest power of two we can divide each value by : the quantized block values are within [-2, ~1.95)

    return clamp(0, 255, bigE + EXP_BIAS) # exponents stored in u_int8 format


def quantize(vector: list[int], exp: int) -> list[int]:
    # scale each block | note: exp is biased w/ 127

    # convert float values in a block into their microscaled values; a value between +- ~1.98 represented as an 8 bit Q2.6 
    # value, which the hardware treats like plain int8s (1.98 = x7F = 64, -1.98 = xFE = -127)
    mxBlock = [round(clamp(LOW_BOUND, UPPER_BOUND, (num / 2**(exp - EXP_BIAS)) * 64)) for num in vector] 
    # note: values won't be greater than 127 due to the way the block exponent is calculated, but values below -127 saturate to mimic hardware int8 clamping  

    return mxBlock



def mxDotProd(wBlock: list[int], aBlock: list[int], eW: int, eA: int) -> int:
    # calculate the dot product of a weight and activation block 

    unscaledProd = sum([weight * activation for weight, activation in zip(wBlock, aBlock)])

    return unscaledProd * 2**(eW + eA - 2*EXP_BIAS - 2*FRAC_BITS) 



def mxint8test(wBlock: list[int], aBlock: list[int]) -> int:
    # microscale and quantize blocks, calculate their dot prod and return unscaled result

    eW = getE(wBlock)
    eA = getE(aBlock)

    f_wBlock = quantize(wBlock, eW)
    f_aBlock = quantize(aBlock, eA)


    print(f"Quantized Weights: {f_wBlock}\nQuantized Activations: {f_aBlock} \n\n")

    mx_test = mxDotProd(f_aBlock, f_wBlock, eA, eW)

    return mx_test


def refTest(weights: list[float], acts: list[float]) -> float:
    # standard float dot product for comparison
    prod = sum([w * a for w, a in zip(weights, acts)])

    return prod



def random_test():
    # generate random weight & activation blocks, microscale and quantize, calculate their unscaled dot product, and compare to full-precision reference
    weights = []
    acts = []

    for _ in range(BLOCK_SIZE):
        weights.append(random.gauss(0, 1))
        acts.append(random.gauss(0, 1))


    print(f"Raw Weights: {weights} \nRaw Activations: {acts}\n\n")

    mx_res = mxint8test(weights, acts)
    print(f"mxint8 result: {mx_res}\n")

    ref_res = refTest(weights, acts)
    print(f"expected result: {ref_res}\n")


    # use abs for normalized error analysis
    weights = [abs(w) for w in weights]
    acts = [abs(a) for a in acts]
    ref_mag = refTest(weights, acts)
    print(f"Error: {(mx_res - ref_res) / ref_mag * 100}% | Absolute error: {mx_res - ref_res}")


if __name__ == '__main__':
    random_test()

